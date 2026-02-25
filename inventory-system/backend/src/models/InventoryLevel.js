const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');
const Product = require('./Product');
const Location = require('./Location');

const InventoryLevel = sequelize.define('InventoryLevel', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  product_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: Product,
      key: 'id'
    }
  },
  location_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: Location,
      key: 'id'
    }
  },
  quantity: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false,
    defaultValue: 0,
    validate: {
      min: 0
    }
  },
  reserved_quantity: {
    type: DataTypes.DECIMAL(15, 3),
    allowNull: false,
    defaultValue: 0,
    validate: {
      min: 0
    }
  },
  available_quantity: {
    type: DataTypes.VIRTUAL,
    get() {
      return parseFloat(this.quantity) - parseFloat(this.reserved_quantity);
    }
  }
}, {
  tableName: 'inventory_levels',
  timestamps: true,
  indexes: [
    { fields: ['product_id', 'location_id'], unique: true },
    { fields: ['product_id'] },
    { fields: ['location_id'] }
  ]
});

// Define associations
InventoryLevel.belongsTo(Product, { foreignKey: 'product_id' });
InventoryLevel.belongsTo(Location, { foreignKey: 'location_id' });
Product.hasMany(InventoryLevel, { foreignKey: 'product_id' });
Location.hasMany(InventoryLevel, { foreignKey: 'location_id' });

module.exports = InventoryLevel;
