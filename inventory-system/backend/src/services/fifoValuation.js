const { Op } = require('sequelize');
const FIFOLayer = require('../models/FIFOLayer');
const StockLedger = require('../models/StockLedger');

/**
 * FIFO Valuation Service
 * Manages cost layers and allocates costs using First-In-First-Out method
 */
class FIFOValuationService {
  
  /**
   * Create a new FIFO layer when stock is received
   * @param {Object} params - Layer parameters
   * @param {number} params.product_id - Product ID
   * @param {string} params.lot_number - Optional lot/batch number
   * @param {number} params.unit_cost - Cost per unit
   * @param {number} params.quantity - Quantity received
   * @param {Date} params.expiry_date - Optional expiry date
   * @returns {Promise<FIFOLayer>}
   */
  async createLayer({ product_id, lot_number, unit_cost, quantity, expiry_date }) {
    return FIFOLayer.create({
      product_id,
      lot_number,
      unit_cost,
      quantity_received: quantity,
      quantity_remaining: quantity,
      expiry_date,
      received_date: new Date()
    });
  }

  /**
   * Get available (non-consumed) layers for a product, ordered by FIFO
   * @param {number} product_id 
   * @returns {Promise<FIFOLayer[]>}
   */
  async getAvailableLayers(product_id) {
    return FIFOLayer.findAll({
      where: {
        product_id,
        quantity_remaining: { [Op.gt]: 0 },
        is_fully_consumed: false
      },
      order: [['received_date', 'ASC'], ['id', 'ASC']]
    });
  }

  /**
   * Calculate FIFO cost allocation for a stock issue
   * Consumes from oldest layers first
   * 
   * @param {number} product_id - Product to issue
   * @param {number} quantity_needed - Quantity to issue
   * @returns {Promise<Object>} - { total_cost, layers_consumed: [{layer_id, quantity, unit_cost}] }
   */
  async calculateIssueCost(product_id, quantity_needed) {
    const layers = await this.getAvailableLayers(product_id);
    
    if (layers.length === 0) {
      throw new Error(`No FIFO layers available for product ${product_id}`);
    }

    let remaining = parseFloat(quantity_needed);
    let total_cost = 0;
    const layers_consumed = [];

    for (const layer of layers) {
      if (remaining <= 0) break;

      const available = parseFloat(layer.quantity_remaining);
      const consume = Math.min(remaining, available);

      total_cost += consume * parseFloat(layer.unit_cost);
      layers_consumed.push({
        layer_id: layer.id,
        quantity: consume,
        unit_cost: parseFloat(layer.unit_cost),
        lot_number: layer.lot_number
      });

      remaining -= consume;
    }

    if (remaining > 0) {
      const totalAvailable = layers.reduce((sum, l) => sum + parseFloat(l.quantity_remaining), 0);
      throw new Error(
        `Insufficient stock in FIFO layers for product ${product_id}. ` +
        `Needed: ${quantity_needed}, Available: ${totalAvailable}`
      );
    }

    const avg_cost = total_cost / parseFloat(quantity_needed);

    return {
      total_cost: parseFloat(total_cost.toFixed(4)),
      unit_cost: parseFloat(avg_cost.toFixed(4)),
      layers_consumed
    };
  }

  /**
   * Commit the FIFO consumption (update layer quantities)
   * Call this AFTER successful inventory update
   * 
   * @param {Array} layers_consumed - Array from calculateIssueCost
   * @param {Object} transaction - Sequelize transaction
   */
  async commitConsumption(layers_consumed, transaction) {
    for (const consumed of layers_consumed) {
      const layer = await FIFOLayer.findByPk(consumed.layer_id, { transaction });
      if (!layer) {
        throw new Error(`FIFO layer ${consumed.layer_id} not found`);
      }

      const newRemaining = parseFloat(layer.quantity_remaining) - consumed.quantity;
      
      await layer.update({
        quantity_remaining: newRemaining,
        is_fully_consumed: newRemaining <= 0
      }, { transaction });
    }
  }

  /**
   * Get current inventory valuation for a product
   * @param {number} product_id 
   * @returns {Promise<Object>} - { total_quantity, total_value, layers: [] }
   */
  async getProductValuation(product_id) {
    const layers = await this.getAvailableLayers(product_id);
    
    let total_quantity = 0;
    let total_value = 0;

    const layerDetails = layers.map(layer => {
      const qty = parseFloat(layer.quantity_remaining);
      const cost = parseFloat(layer.unit_cost);
      const value = qty * cost;
      
      total_quantity += qty;
      total_value += value;

      return {
        lot_number: layer.lot_number,
        received_date: layer.received_date,
        quantity: qty,
        unit_cost: cost,
        value: parseFloat(value.toFixed(4)),
        expiry_date: layer.expiry_date
      };
    });

    return {
      product_id,
      total_quantity: parseFloat(total_quantity.toFixed(3)),
      total_value: parseFloat(total_value.toFixed(4)),
      layers: layerDetails
    };
  }

  /**
   * Rollback a consumption (for reversals/corrections)
   * Creates a compensating entry
   * 
   * @param {number} product_id 
   * @param {Array} original_consumption - Original layers_consumed array
   * @param {Object} transaction 
   */
  async rollbackConsumption(product_id, original_consumption, transaction) {
    for (const consumed of original_consumption) {
      const layer = await FIFOLayer.findByPk(consumed.layer_id, { transaction });
      if (layer) {
        const newRemaining = parseFloat(layer.quantity_remaining) + consumed.quantity;
        await layer.update({
          quantity_remaining: newRemaining,
          is_fully_consumed: false
        }, { transaction });
      }
    }
  }
}

module.exports = new FIFOValuationService();
