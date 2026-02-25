const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Product = require('./Product');
const Location = require('./Location');

const StockLedger = sequelize.define('StockLedger', {
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
  location_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: { model: Location, key: 'id' }
  },
  movement_type: {
    type: DataTypes.ENUM('RECEIPT', 'ISSUE', 'TRANSFER_IN', 'TRANSFER_OUT', 'ADJUSTMENT'),
    allowNull: false
  },
  quantity: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false
  },
  unit_cost: {
    type: DataTypes.DECIMAL(15, 4),
    allowNull: true
  },
  total_cost: {
    type: DataTypes.DECIMAL(15, 4),
    allowNull: true
  },
  reference_id: {
    type: DataTypes.STRING(50),
    allowNull: true // PO number, Transfer ID, etc.
  },
  reference_type: {
    type: DataTypes.STRING(50),
    allowNull: true
  },
  notes: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  performed_by: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  running_balance: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false
  }
}, {
  tableName: 'stock_ledger',
  timestamps: true,
  updatedAt: false, // Immutable - no updates allowed
  indexes: [
    { fields: ['product_id', 'location_id'] },
    { fields: ['movement_type'] },
    { fields: ['created_at'] },
    { fields: ['reference_id'] }
  ]
});

StockLedger.belongsTo(Product, { foreignKey: 'product_id' });
StockLedger.belongsTo(Location, { foreignKey: 'location_id' });

module.exports = StockLedger;
