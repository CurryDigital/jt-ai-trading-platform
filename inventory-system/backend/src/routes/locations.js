const express = require('express');
const { body, param } = require('express-validator');
const Location = require('../models/Location');

const router = express.Router();

// GET /api/locations - List all locations
router.get('/', async (req, res) => {
  try {
    const { type, is_active } = req.query;
    const where = {};
    
    if (type) where.type = type;
    if (is_active !== undefined) where.is_active = is_active === 'true';

    const locations = await Location.findAll({
      where,
      order: [['name', 'ASC']]
    });

    res.json({ success: true, count: locations.length, data: locations });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/locations/:id - Get single location
router.get('/:id', async (req, res) => {
  try {
    const location = await Location.findByPk(req.params.id);
    if (!location) {
      return res.status(404).json({ success: false, error: 'Location not found' });
    }
    res.json({ success: true, data: location });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/locations - Create location
router.post('/', [
  body('code').trim().isLength({ min: 1, max: 20 }),
  body('name').trim().isLength({ min: 1, max: 100 }),
  body('type').optional().isIn(['WAREHOUSE', 'STORE', 'VIRTUAL', 'SUPPLIER'])
], async (req, res) => {
  try {
    const location = await Location.create(req.body);
    res.status(201).json({ success: true, data: location });
  } catch (error) {
    if (error.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ success: false, error: 'Location code already exists' });
    }
    res.status(500).json({ success: false, error: error.message });
  }
});

// PUT /api/locations/:id - Update location
router.put('/:id', async (req, res) => {
  try {
    const location = await Location.findByPk(req.params.id);
    if (!location) {
      return res.status(404).json({ success: false, error: 'Location not found' });
    }

    await location.update(req.body);
    res.json({ success: true, data: location });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
