const express = require('express');
const { body, param, validationResult } = require('express-validator');
const Product = require('../models/Product');
const InventoryLevel = require('../models/InventoryLevel');
const Location = require('../models/Location');

const router = express.Router();

// Validation middleware
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  next();
};

// GET /api/products - List all products
router.get('/', async (req, res) => {
  try {
    const { category, is_active, search } = req.query;
    const where = {};
    
    if (category) where.category = category;
    if (is_active !== undefined) where.is_active = is_active === 'true';
    if (search) {
      where[Op.or] = [
        { sku: { [Op.iLike]: `%${search}%` } },
        { name: { [Op.iLike]: `%${search}%` } }
      ];
    }

    const products = await Product.findAll({
      where,
      order: [['name', 'ASC']],
      include: [{
        model: InventoryLevel,
        include: [Location]
      }]
    });

    res.json({ success: true, count: products.length, data: products });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/products/:id - Get single product
router.get('/:id', [
  param('id').isInt(),
  handleValidationErrors
], async (req, res) => {
  try {
    const product = await Product.findByPk(req.params.id, {
      include: [{
        model: InventoryLevel,
        include: [Location]
      }]
    });

    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/products - Create product
router.post('/', [
  body('sku').trim().isLength({ min: 1, max: 50 }),
  body('name').trim().isLength({ min: 1, max: 255 }),
  body('unit_of_measure').optional().trim(),
  body('reorder_point').optional().isFloat({ min: 0 }),
  body('max_stock').optional().isFloat({ min: 0 }),
  handleValidationErrors
], async (req, res) => {
  try {
    const product = await Product.create(req.body);
    res.status(201).json({ success: true, data: product });
  } catch (error) {
    if (error.name === 'SequelizeUniqueConstraintError') {
      return res.status(409).json({ success: false, error: 'SKU already exists' });
    }
    res.status(500).json({ success: false, error: error.message });
  }
});

// PUT /api/products/:id - Update product
router.put('/:id', [
  param('id').isInt(),
  body('name').optional().trim().isLength({ min: 1 }),
  body('reorder_point').optional().isFloat({ min: 0 }),
  body('max_stock').optional().isFloat({ min: 0 }),
  handleValidationErrors
], async (req, res) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    await product.update(req.body);
    res.json({ success: true, data: product });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// DELETE /api/products/:id - Soft delete product
router.delete('/:id', [
  param('id').isInt(),
  handleValidationErrors
], async (req, res) => {
  try {
    const product = await Product.findByPk(req.params.id);
    if (!product) {
      return res.status(404).json({ success: false, error: 'Product not found' });
    }

    await product.destroy(); // Soft delete
    res.json({ success: true, message: 'Product archived' });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
