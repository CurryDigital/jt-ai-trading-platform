const { Op } = require('sequelize');
const Product = require('../models/Product');
const InventoryLevel = require('../models/InventoryLevel');
const Location = require('../models/Location');

/**
 * Low Stock Alert Service
 * Implements 15% threshold logic for inventory alerts
 * 
 * Alert triggers when: current_quantity <= reorder_point * 0.15
 */
class LowStockAlertService {
  constructor() {
    this.threshold = parseFloat(process.env.LOW_STOCK_THRESHOLD) || 0.15;
  }

  /**
   * Check if a specific inventory level should trigger an alert
   * @param {InventoryLevel} inventoryLevel 
   * @param {Product} product 
   * @returns {Object} - { is_alert, severity, message, suggested_order_qty }
   */
  checkAlertStatus(inventoryLevel, product) {
    const currentQty = parseFloat(inventoryLevel.quantity);
    const reorderPoint = parseFloat(product.reorder_point);
    const maxStock = parseFloat(product.max_stock);

    // Calculate threshold (15% of reorder point)
    const alertThreshold = reorderPoint * this.threshold;

    // Also check against reorder point for standard reorder alert
    const isLowStock = currentQty <= alertThreshold;
    const isReorderPoint = currentQty <= reorderPoint && currentQty > alertThreshold;

    let result = {
      is_alert: false,
      severity: 'NONE',
      message: null,
      current_quantity: currentQty,
      reorder_point: reorderPoint,
      threshold_value: parseFloat(alertThreshold.toFixed(3)),
      suggested_order_qty: 0
    };

    if (isLowStock) {
      const suggestedQty = Math.max(0, maxStock - currentQty);
      result = {
        ...result,
        is_alert: true,
        severity: 'CRITICAL',
        message: `CRITICAL: Stock level (${currentQty}) is at or below 15% threshold (${alertThreshold.toFixed(2)})`,
        suggested_order_qty: parseFloat(suggestedQty.toFixed(3))
      };
    } else if (isReorderPoint) {
      const suggestedQty = Math.max(0, maxStock - currentQty);
      result = {
        ...result,
        is_alert: true,
        severity: 'WARNING',
        message: `WARNING: Stock level (${currentQty}) has reached reorder point (${reorderPoint})`,
        suggested_order_qty: parseFloat(suggestedQty.toFixed(3))
      };
    }

    return result;
  }

  /**
   * Get all low stock alerts across all locations
   * @param {Object} options - Filter options
   * @param {number} options.location_id - Filter by specific location
   * @param {string} options.severity - Filter by severity (CRITICAL, WARNING)
   * @returns {Promise<Array>}
   */
  async getAllAlerts(options = {}) {
    const whereClause = {};
    if (options.location_id) {
      whereClause.location_id = options.location_id;
    }

    const inventoryLevels = await InventoryLevel.findAll({
      where: whereClause,
      include: [
        { model: Product, required: true },
        { model: Location, required: true }
      ]
    });

    const alerts = [];

    for (const level of inventoryLevels) {
      const alertCheck = this.checkAlertStatus(level, level.Product);
      
      if (alertCheck.is_alert) {
        // Apply severity filter if specified
        if (options.severity && alertCheck.severity !== options.severity) {
          continue;
        }

        alerts.push({
          inventory_id: level.id,
          product_id: level.product_id,
          product_sku: level.Product.sku,
          product_name: level.Product.name,
          location_id: level.location_id,
          location_name: level.Location.name,
          current_quantity: alertCheck.current_quantity,
          reorder_point: alertCheck.reorder_point,
          threshold_value: alertCheck.threshold_value,
          max_stock: parseFloat(level.Product.max_stock),
          severity: alertCheck.severity,
          message: alertCheck.message,
          suggested_order_qty: alertCheck.suggested_order_qty,
          unit_of_measure: level.Product.unit_of_measure,
          updated_at: level.updatedAt
        });
      }
    }

    // Sort by severity (CRITICAL first), then by current quantity ascending
    return alerts.sort((a, b) => {
      if (a.severity === 'CRITICAL' && b.severity !== 'CRITICAL') return -1;
      if (a.severity !== 'CRITICAL' && b.severity === 'CRITICAL') return 1;
      return a.current_quantity - b.current_quantity;
    });
  }

  /**
   * Get alert summary counts by severity
   * @returns {Promise<Object>}
   */
  async getAlertSummary() {
    const allAlerts = await this.getAllAlerts();
    
    return {
      total: allAlerts.length,
      critical: allAlerts.filter(a => a.severity === 'CRITICAL').length,
      warning: allAlerts.filter(a => a.severity === 'WARNING').length,
      alerts: allAlerts.slice(0, 10) // Top 10 for dashboard
    };
  }

  /**
   * Get alerts for a specific product across all locations
   * @param {number} product_id 
   * @returns {Promise<Array>}
   */
  async getAlertsByProduct(product_id) {
    const inventoryLevels = await InventoryLevel.findAll({
      where: { product_id },
      include: [Product, Location]
    });

    return inventoryLevels
      .map(level => ({
        ...this.checkAlertStatus(level, level.Product),
        location: level.Location.name,
        location_id: level.location_id
      }))
      .filter(alert => alert.is_alert);
  }
}

module.exports = new LowStockAlertService();
