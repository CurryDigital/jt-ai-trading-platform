const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Product = require('./Product');
const Location = require('./Location');

const StockMovement = sequelize.define('StockMovement', {
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
  source_location_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: { model: Location, key: 'id' }
  },
  destination_location_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: { model: Location, key: 'id' }
  },
  movement_type: {
    type: DataTypes.ENUM('RECEIPT', 'ISSUE', 'TRANSFER', 'ADJUSTMENT'),
    allowNull: false
  },
  quantity: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false,
    validate: { min: 0.001 }
  },
  unit_cost: {
    type: DataTypes.DECIMAL(15, 4),
    allowNull: true
  },
  total_cost: {
    type: DataTypes.DECIMAL(15, 4),
    allowNull: true
  },
  lot_number: {
    type: DataTypes.STRING(50),
    allowNull: true
  },
  reference_id: {
    type: DataTypes.STRING(50),
    allowNull: true
  },
  reason: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  performed_by: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  status: {
    type: DataTypes.ENUM('PENDING', 'COMPLETED', 'CANCELLED'),
    allowNull: false,
    defaultValue: 'PENDING'
  }
}, {
  tableName: 'stock_movements',
  timestamps: true,
  indexes: [
    { fields: ['product_id'] },
    { fields: ['movement_type'] },
    { fields: ['status'] },
    { fields: ['created_at'] }
  ]
});

StockMovement.belongsTo(Product, { foreignKey: 'product_id' });
StockMovement.belongsTo(Location, { as: 'SourceLocation', foreignKey: 'source_location_id' });
StockMovement.belongsTo(Location, { as: 'DestinationLocation', foreignKey: 'destination_location_id' });

module.exports = StockMovement;
