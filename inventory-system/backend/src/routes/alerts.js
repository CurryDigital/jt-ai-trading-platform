const express = require('express');
const { query } = require('express-validator');
const alertService = require('../services/lowStockAlert');

const router = express.Router();

// GET /api/alerts - Get all low stock alerts
router.get('/', async (req, res) => {
  try {
    const { location_id, severity } = req.query;
    const alerts = await alertService.getAllAlerts({ location_id, severity });
    
    res.json({
      success: true,
      count: alerts.length,
      data: alerts
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/alerts/summary - Get alert counts only
router.get('/summary', async (req, res) => {
  try {
    const summary = await alertService.getAlertSummary();
    res.json({ success: true, data: summary });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/alerts/product/:product_id - Get alerts for specific product
router.get('/product/:product_id', async (req, res) => {
  try {
    const alerts = await alertService.getAlertsByProduct(req.params.product_id);
    res.json({ success: true, data: alerts });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
