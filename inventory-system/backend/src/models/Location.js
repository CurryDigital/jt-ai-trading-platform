const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const Location = sequelize.define('Location', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  code: {
    type: DataTypes.STRING(20),
    allowNull: false,
    unique: true
  },
  name: {
    type: DataTypes.STRING(100),
    allowNull: false
  },
  type: {
    type: DataTypes.ENUM('WAREHOUSE', 'STORE', 'VIRTUAL', 'SUPPLIER'),
    allowNull: false,
    defaultValue: 'WAREHOUSE'
  },
  address: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  is_active: {
    type: DataTypes.BOOLEAN,
    allowNull: false,
    defaultValue: true
  }
}, {
  tableName: 'locations',
  timestamps: true,
  indexes: [
    { fields: ['code'] },
    { fields: ['type'] }
  ]
});

module.exports = Location;
