const pool = require('../config/db');

const getAllTickets = async ({ status, priority, search }) => {
  let query = `
    SELECT 
      id,
      title,
      description,
      status,
      priority,
      created_at,
      updated_at
    FROM tickets
    WHERE 1 = 1
  `;

  const params = [];

  if (status) {
    query += ' AND status = ?';
    params.push(status);
  }

  if (priority) {
    query += ' AND priority = ?';
    params.push(priority);
  }

  if (search) {
    query += ' AND (title LIKE ? OR description LIKE ?)';
    params.push(`%${search}%`, `%${search}%`);
  }

  query += ' ORDER BY created_at DESC';

  const [rows] = await pool.query(query, params);

  return rows;
};

const getTicketById = async (id) => {
  const [rows] = await pool.query(
    `
    SELECT 
      id,
      title,
      description,
      status,
      priority,
      created_at,
      updated_at
    FROM tickets
    WHERE id = ?
    `,
    [id]
  );

  return rows[0];
};

const createTicket = async ({ title, description, status, priority }) => {
  const [result] = await pool.query(
    `
    INSERT INTO tickets (title, description, status, priority)
    VALUES (?, ?, ?, ?)
    `,
    [title, description, status || 'pendiente', priority || 'media']
  );

  return getTicketById(result.insertId);
};

const updateTicket = async (id, { title, description, status, priority }) => {
  await pool.query(
    `
    UPDATE tickets
    SET 
      title = ?,
      description = ?,
      status = ?,
      priority = ?
    WHERE id = ?
    `,
    [title, description, status, priority, id]
  );

  return getTicketById(id);
};

const updateTicketStatus = async (id, status) => {
  await pool.query(
    `
    UPDATE tickets
    SET status = ?
    WHERE id = ?
    `,
    [status, id]
  );

  return getTicketById(id);
};

const deleteTicket = async (id) => {
  const [result] = await pool.query(
    `
    DELETE FROM tickets
    WHERE id = ?
    `,
    [id]
  );

  return result.affectedRows > 0;
};

module.exports = {
  getAllTickets,
  getTicketById,
  createTicket,
  updateTicket,
  updateTicketStatus,
  deleteTicket,
};