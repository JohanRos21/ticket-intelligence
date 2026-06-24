const express = require('express');
const cors = require('cors');
require('dotenv').config();

const pool = require('./config/db');
const ticketRoutes = require('./routes/ticketRoutes');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api/tickets', ticketRoutes);

app.get('/', (req, res) => {
  res.json({
    message: 'API REST de Tickets funcionando correctamente',
  });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
});

app.get('/db-test', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT 1 + 1 AS result');

    res.json({
      message: 'Conexión a MySQL correcta',
      result: rows[0].result,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al conectar con MySQL',
      error: error.message,
    });
  }
});