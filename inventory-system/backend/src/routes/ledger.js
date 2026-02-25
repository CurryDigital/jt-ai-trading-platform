const express = require('express');
const { param, query } = require('express-validator');
const StockLedger = require('../models/StockLedger');
const Product = require('../models/Product');
const Location = require('../models/Location');
const { Op } = require('sequelize');

const router = express.Router();

// GET /api/ledger - Query stock ledger
router.get('/', async (req, res) => {
  try {
    const { 
      product_id, 
      location_id, 
      movement_type, 
      start_date, 
      end_date,
      page = 1,
      limit = 50
    } = req.query;

    const where = {};
    if (product_id) where.product_id = product_id;
    if (location_id) where.location_id = location_id;
    if (movement_type) where.movement_type = movement_type;
    
    if (start_date || end_date) {
      where.created_at = {};
      if (start_date) where.created_at[Op.gte] = new Date(start_date);
      if (end_date) where.created_at[Op.lte] = new Date(end_date);
    }

    const offset = (page - 1) * limit;

    const { count, rows } = await StockLedger.findAndCountAll({
      where,
      include: [Product, Location],
      order: [['created_at', 'DESC']],
      limit: parseInt(limit),
      offset: parseInt(offset)
    });

    res.json({
      success: true,
      count,
      pages: Math.ceil(count / limit),
      current_page: parseInt(page),
      data: rows
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/ledger/product/:product_id - Get ledger for specific product
router.get('/product/:product_id', [
  param('product_id').isInt()
], async (req, res) => {
  try {
    const entries = await StockLedger.findAll({
      where: { product_id: req.params.product_id },
      include: [Location],
      order: [['created_at', 'DESC']]
    });

    res.json({ success: true, count: entries.length, data: entries });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
