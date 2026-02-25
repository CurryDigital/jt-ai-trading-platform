const express = require('express');
const { body, param, query, validationResult } = require('express-validator');
const stockMovementService = require('../services/stockMovement');
const fifoService = require('../services/fifoValuation');
const InventoryLevel = require('../models/InventoryLevel');
const Product = require('../models/Product');
const Location = require('../models/Location');

const router = express.Router();

const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// GET /api/inventory - Get inventory levels
router.get('/', async (req, res) => {
  try {
    const { location_id, product_id, low_stock } = req.query;
    const where = {};
    
    if (location_id) where.location_id = location_id;
    if (product_id) where.product_id = product_id;

    const include = [
      { model: Product, required: true },
      { model: Location, required: true }
    ];

    let inventory = await InventoryLevel.findAll({ where, include });

    // Apply low stock filter if requested
    if (low_stock === 'true') {
      const alertService = require('../services/lowStockAlert');
      inventory = inventory.filter(level => {
        const check = alertService.checkAlertStatus(level, level.Product);
        return check.is_alert;
      });
    }

    res.json({ success: true, count: inventory.length, data: inventory });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/inventory/summary - Dashboard summary
router.get('/summary', async (req, res) => {
  try {
    const [totalProducts, totalLocations, totalQuantity] = await Promise.all([
      Product.count({ where: { is_active: true } }),
      Location.count({ where: { is_active: true } }),
      InventoryLevel.sum('quantity')
    ]);

    const alertService = require('../services/lowStockAlert');
    const alerts = await alertService.getAlertSummary();

    res.json({
      success: true,
      data: {
        total_products: totalProducts,
        total_locations: totalLocations,
        total_quantity: totalQuantity || 0,
        alerts
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/inventory/receive - Receive stock
router.post('/receive', [
  body('product_id').isInt(),
  body('location_id').isInt(),
  body('quantity').isFloat({ min: 0.001 }),
  body('unit_cost').isFloat({ min: 0 }),
  body('performed_by').trim().notEmpty(),
  body('lot_number').optional().trim(),
  body('expiry_date').optional().isISO8601(),
  handleValidationErrors
], async (req, res) => {
  try {
    const result = await stockMovementService.receiveStock(req.body);
    res.status(201).json({ success: true, data: result });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// POST /api/inventory/issue - Issue stock
router.post('/issue', [
  body('product_id').isInt(),
  body('location_id').isInt(),
  body('quantity').isFloat({ min: 0.001 }),
  body('performed_by').trim().notEmpty(),
  body('reason').optional().trim(),
  handleValidationErrors
], async (req, res) => {
  try {
    const result = await stockMovementService.issueStock(req.body);
    res.status(201).json({ success: true, data: result });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// POST /api/inventory/transfer - Transfer stock between locations
router.post('/transfer', [
  body('product_id').isInt(),
  body('source_location_id').isInt(),
  body('destination_location_id').isInt(),
  body('quantity').isFloat({ min: 0.001 }),
  body('performed_by').trim().notEmpty(),
  handleValidationErrors
], async (req, res) => {
  try {
    const result = await stockMovementService.transferStock(req.body);
    res.status(201).json({ success: true, data: result });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// POST /api/inventory/adjust - Adjust stock
router.post('/adjust', [
  body('product_id').isInt(),
  body('location_id').isInt(),
  body('adjustment_qty').isFloat(),
  body('performed_by').trim().notEmpty(),
  body('reason').trim().notEmpty(),
  handleValidationErrors
], async (req, res) => {
  try {
    const result = await stockMovementService.adjustStock(req.body);
    res.status(201).json({ success: true, data: result });
  } catch (error) {
    res.status(400).json({ success: false, error: error.message });
  }
});

// GET /api/inventory/valuation/:product_id - Get FIFO valuation
router.get('/valuation/:product_id', [
  param('product_id').isInt(),
  handleValidationErrors
], async (req, res) => {
  try {
    const valuation = await fifoService.getProductValuation(req.params.product_id);
    res.json({ success: true, data: valuation });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
