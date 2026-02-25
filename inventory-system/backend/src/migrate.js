const { sequelize } = require('./config/database');

// Import all models to register associations
require('./models/Product');
require('./models/Location');
require('./models/InventoryLevel');
require('./models/StockLedger');
require('./models/FIFOLayer');
require('./models/StockMovement');

const migrate = async () => {
  try {
    console.log('🔄 Running database migrations...');
    
    // Sync all models (creates tables if not exist)
    // alter: true updates tables to match models
    await sequelize.sync({ alter: true });
    
    console.log('✅ Database migrations completed successfully');
    
    // Seed default locations if none exist
    const Location = require('./models/Location');
    const count = await Location.count();
    
    if (count === 0) {
      console.log('🌱 Seeding default locations...');
      await Location.bulkCreate([
        { code: 'MAIN', name: 'Main Warehouse', type: 'WAREHOUSE' },
        { code: 'RETAIL', name: 'Retail Store', type: 'STORE' },
        { code: 'VIRTUAL', name: 'Virtual Location', type: 'VIRTUAL' }
      ]);
      console.log('✅ Default locations created');
    }
    
    process.exit(0);
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  }
};

migrate();
