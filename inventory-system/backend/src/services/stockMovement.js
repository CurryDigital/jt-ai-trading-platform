const { sequelize } = require('../config/database');
const InventoryLevel = require('../models/InventoryLevel');
const StockLedger = require('../models/StockLedger');
const StockMovement = require('../models/StockMovement');
const Product = require('../models/Product');
const Location = require('../models/Location');
const fifoService = require('./fifoValuation');

/**
 * Stock Movement Service
 * Orchestrates stock receipts, issues, and transfers
 * Enforces data integrity through transactions
 */
class StockMovementService {

  /**
   * Receive stock into inventory (creates FIFO layer)
   * @param {Object} params
   * @returns {Promise<Object>} - { movement, ledger_entry, fifo_layer }
   */
  async receiveStock({
    product_id,
    location_id,
    quantity,
    unit_cost,
    lot_number,
    expiry_date,
    reference_id,
    reference_type = 'PURCHASE_ORDER',
    performed_by,
    reason
  }) {
    const transaction = await sequelize.transaction();

    try {
      // 1. Create or update inventory level
      let [inventoryLevel, created] = await InventoryLevel.findOrCreate({
        where: { product_id, location_id },
        defaults: { quantity: 0, reserved_quantity: 0 },
        transaction
      });

      const newQuantity = parseFloat(inventoryLevel.quantity) + parseFloat(quantity);
      await inventoryLevel.update({ quantity: newQuantity }, { transaction });

      // 2. Create FIFO layer for cost tracking
      const fifoLayer = await fifoService.createLayer({
        product_id,
        lot_number,
        unit_cost,
        quantity,
        expiry_date
      });
      // Note: FIFO layer is independent transaction, committed immediately

      // 3. Create stock movement record
      const movement = await StockMovement.create({
        product_id,
        destination_location_id: location_id,
        movement_type: 'RECEIPT',
        quantity,
        unit_cost,
        total_cost: parseFloat(quantity) * parseFloat(unit_cost),
        lot_number,
        reference_id,
        reference_type,
        reason,
        performed_by,
        status: 'COMPLETED'
      }, { transaction });

      // 4. Create immutable ledger entry
      const ledgerEntry = await StockLedger.create({
        product_id,
        location_id,
        movement_type: 'RECEIPT',
        quantity,
        unit_cost,
        total_cost: parseFloat(quantity) * parseFloat(unit_cost),
        reference_id,
        reference_type,
        notes: reason,
        performed_by,
        running_balance: newQuantity
      }, { transaction });

      await transaction.commit();

      return {
        movement,
        ledger_entry: ledgerEntry,
        fifo_layer: fifoLayer,
        inventory_level: inventoryLevel
      };

    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }

  /**
   * Issue stock from inventory (consumes FIFO layers)
   * @param {Object} params
   * @returns {Promise<Object>} - { movement, ledger_entry, fifo_consumed }
   */
  async issueStock({
    product_id,
    location_id,
    quantity,
    reference_id,
    reference_type = 'SALES_ORDER',
    performed_by,
    reason
  }) {
    const transaction = await sequelize.transaction();

    try {
      // 1. Validate sufficient stock
      const inventoryLevel = await InventoryLevel.findOne({
        where: { product_id, location_id },
        transaction
      });

      if (!inventoryLevel || parseFloat(inventoryLevel.quantity) < parseFloat(quantity)) {
        throw new Error(
          `Insufficient stock. Available: ${inventoryLevel?.quantity || 0}, Requested: ${quantity}`
        );
      }

      // 2. Calculate FIFO cost allocation
      const fifoResult = await fifoService.calculateIssueCost(product_id, quantity);

      // 3. Update inventory level
      const newQuantity = parseFloat(inventoryLevel.quantity) - parseFloat(quantity);
      await inventoryLevel.update({ quantity: newQuantity }, { transaction });

      // 4. Commit FIFO consumption
      await fifoService.commitConsumption(fifoResult.layers_consumed, transaction);

      // 5. Create stock movement record
      const movement = await StockMovement.create({
        product_id,
        source_location_id: location_id,
        movement_type: 'ISSUE',
        quantity: -quantity, // Negative for issues
        unit_cost: fifoResult.unit_cost,
        total_cost: -fifoResult.total_cost,
        reference_id,
        reference_type,
        reason,
        performed_by,
        status: 'COMPLETED'
      }, { transaction });

      // 6. Create immutable ledger entry
      const ledgerEntry = await StockLedger.create({
        product_id,
        location_id,
        movement_type: 'ISSUE',
        quantity: -quantity,
        unit_cost: fifoResult.unit_cost,
        total_cost: -fifoResult.total_cost,
        reference_id,
        reference_type,
        notes: reason,
        performed_by,
        running_balance: newQuantity
      }, { transaction });

      await transaction.commit();

      return {
        movement,
        ledger_entry: ledgerEntry,
        fifo_consumed: fifoResult.layers_consumed,
        total_cost: fifoResult.total_cost,
        unit_cost: fifoResult.unit_cost
      };

    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }

  /**
   * Transfer stock between locations
   * Creates two movements: ISSUE from source, RECEIPT to destination
   * @param {Object} params
   * @returns {Promise<Object>} - { issue_result, receipt_result }
   */
  async transferStock({
    product_id,
    source_location_id,
    destination_location_id,
    quantity,
    reference_id,
    performed_by,
    reason
  }) {
    // Validate different locations
    if (source_location_id === destination_location_id) {
      throw new Error('Source and destination locations must be different');
    }

    // First issue from source
    const issueResult = await this.issueStock({
      product_id,
      location_id: source_location_id,
      quantity,
      reference_id,
      reference_type: 'TRANSFER',
      performed_by,
      reason: `Transfer to location ${destination_location_id}: ${reason || ''}`
    });

    // Then receive at destination (using the same cost)
    const receiptResult = await this.receiveStock({
      product_id,
      location_id: destination_location_id,
      quantity,
      unit_cost: issueResult.unit_cost,
      lot_number: issueResult.fifo_consumed[0]?.lot_number,
      reference_id,
      reference_type: 'TRANSFER',
      performed_by,
      reason: `Transfer from location ${source_location_id}: ${reason || ''}`
    });

    return {
      issue_result: issueResult,
      receipt_result: receiptResult,
      transfer_id: reference_id || `TRF-${Date.now()}`
    };
  }

  /**
   * Adjust inventory (for corrections, damage, etc.)
   * @param {Object} params
   * @returns {Promise<Object>}
   */
  async adjustStock({
    product_id,
    location_id,
    adjustment_qty, // Can be positive or negative
    new_unit_cost, // Optional - for cost adjustments
    reference_id,
    performed_by,
    reason
  }) {
    const transaction = await sequelize.transaction();

    try {
      const inventoryLevel = await InventoryLevel.findOne({
        where: { product_id, location_id },
        transaction
      });

      if (!inventoryLevel) {
        throw new Error('Inventory level not found');
      }

      const currentQty = parseFloat(inventoryLevel.quantity);
      const newQuantity = currentQty + parseFloat(adjustment_qty);

      if (newQuantity < 0) {
        throw new Error('Adjustment would result in negative inventory');
      }

      await inventoryLevel.update({ quantity: newQuantity }, { transaction });

      const movement = await StockMovement.create({
        product_id,
        source_location_id: adjustment_qty < 0 ? location_id : null,
        destination_location_id: adjustment_qty > 0 ? location_id : null,
        movement_type: 'ADJUSTMENT',
        quantity: adjustment_qty,
        unit_cost: new_unit_cost || 0,
        total_cost: new_unit_cost ? adjustment_qty * new_unit_cost : 0,
        reference_id,
        reason,
        performed_by,
        status: 'COMPLETED'
      }, { transaction });

      const ledgerEntry = await StockLedger.create({
        product_id,
        location_id,
        movement_type: 'ADJUSTMENT',
        quantity: adjustment_qty,
        unit_cost: new_unit_cost || 0,
        total_cost: new_unit_cost ? adjustment_qty * new_unit_cost : 0,
        reference_id,
        notes: reason,
        performed_by,
        running_balance: newQuantity
      }, { transaction });

      await transaction.commit();

      return { movement, ledger_entry: ledgerEntry };

    } catch (error) {
      await transaction.rollback();
      throw error;
    }
  }

  /**
   * Get movement history for a product
   * @param {number} product_id 
   * @param {Object} options - Pagination, date filters
   */
  async getMovementHistory(product_id, options = {}) {
    const { limit = 50, offset = 0, start_date, end_date } = options;

    const where = { product_id };
    if (start_date || end_date) {
      where.created_at = {};
      if (start_date) where.created_at[Op.gte] = start_date;
      if (end_date) where.created_at[Op.lte] = end_date;
    }

    return StockMovement.findAndCountAll({
      where,
      include: [
        { model: Location, as: 'SourceLocation' },
        { model: Location, as: 'DestinationLocation' }
      ],
      order: [['created_at', 'DESC']],
      limit,
      offset
    });
  }
}

module.exports = new StockMovementService();
