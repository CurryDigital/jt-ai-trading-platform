const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Product = require('./Product');

const FIFOLayer = sequelize.define('FIFOLayer', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  product_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: { model: Product, key: 'id' }
  },
  lot_number: {
    type: DataTypes.STRING(50),
    allowNull: true
  },
  unit_cost: {
    type: DataTypes.DECIMAL(15, 4),
    allowNull: false,
    validate: { min: 0 }
  },
  quantity_received: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false,
    validate: { min: 0 }
  },
  quantity_remaining: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false,
    validate: { min: 0 }
  },
  expiry_date: {
    type: DataTypes.DATEONLY,
    allowNull: true
  },
  received_date: {
    type: DataTypes.DATE,
    allowNull: false,
    defaultValue: DataTypes.NOW
  },
  is_fully_consumed: {
    type: DataTypes.BOOLEAN,
    allowNull: false,
    defaultValue: false
  }
}, {
  tableName: 'fifo_layers',
  timestamps: true,
  indexes: [
    { fields: ['product_id', 'received_date'] },
    { fields: ['product_id', 'is_fully_consumed'] },
    { fields: ['lot_number'] }
  ]
});

FIFOLayer.belongsTo(Product, { foreignKey: 'product_id' });
Product.hasMany(FIFOLayer, { foreignKey: 'product_id' });

module.exports = FIFOLayer;
