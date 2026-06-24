const ticketModel = require('../models/ticketModel');

const validStatuses = ['pendiente', 'en_proceso', 'resuelto'];
const validPriorities = ['baja', 'media', 'alta'];

const getAllTickets = async (req, res) => {
  try {
    const { status, priority, search } = req.query;

    if (status && !validStatuses.includes(status)) {
      return res.status(400).json({
        message: 'Estado inválido',
        allowedStatuses: validStatuses,
      });
    }

    if (priority && !validPriorities.includes(priority)) {
      return res.status(400).json({
        message: 'Prioridad inválida',
        allowedPriorities: validPriorities,
      });
    }

    const tickets = await ticketModel.getAllTickets({
      status,
      priority,
      search,
    });

    res.json({
      message: 'Tickets obtenidos correctamente',
      filters: {
        status: status || null,
        priority: priority || null,
        search: search || null,
      },
      total: tickets.length,
      data: tickets,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al obtener los tickets',
      error: error.message,
    });
  }
};
const getTicketById = async (req, res) => {
  try {
    const { id } = req.params;

    const ticket = await ticketModel.getTicketById(id);

    if (!ticket) {
      return res.status(404).json({
        message: 'Ticket no encontrado',
      });
    }

    res.json({
      message: 'Ticket obtenido correctamente',
      data: ticket,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al obtener el ticket',
      error: error.message,
    });
  }
};

const createTicket = async (req, res) => {
  try {
    const { title, description, status, priority } = req.body;

    if (!title || title.trim() === '') {
      return res.status(400).json({
        message: 'El título del ticket es obligatorio',
      });
    }

    if (status && !validStatuses.includes(status)) {
      return res.status(400).json({
        message: 'Estado inválido',
        allowedStatuses: validStatuses,
      });
    }

    if (priority && !validPriorities.includes(priority)) {
      return res.status(400).json({
        message: 'Prioridad inválida',
        allowedPriorities: validPriorities,
      });
    }

    const ticket = await ticketModel.createTicket({
      title,
      description,
      status,
      priority,
    });

    res.status(201).json({
      message: 'Ticket creado correctamente',
      data: ticket,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al crear el ticket',
      error: error.message,
    });
  }
};

const updateTicket = async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, status, priority } = req.body;

    const existingTicket = await ticketModel.getTicketById(id);

    if (!existingTicket) {
      return res.status(404).json({
        message: 'Ticket no encontrado',
      });
    }

    if (!title || title.trim() === '') {
      return res.status(400).json({
        message: 'El título del ticket es obligatorio',
      });
    }

    if (!validStatuses.includes(status)) {
      return res.status(400).json({
        message: 'Estado inválido',
        allowedStatuses: validStatuses,
      });
    }

    if (!validPriorities.includes(priority)) {
      return res.status(400).json({
        message: 'Prioridad inválida',
        allowedPriorities: validPriorities,
      });
    }

    const updatedTicket = await ticketModel.updateTicket(id, {
      title,
      description,
      status,
      priority,
    });

    res.json({
      message: 'Ticket actualizado correctamente',
      data: updatedTicket,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al actualizar el ticket',
      error: error.message,
    });
  }
};

const updateTicketStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { status } = req.body;

    const existingTicket = await ticketModel.getTicketById(id);

    if (!existingTicket) {
      return res.status(404).json({
        message: 'Ticket no encontrado',
      });
    }

    if (!status || !validStatuses.includes(status)) {
      return res.status(400).json({
        message: 'Estado inválido',
        allowedStatuses: validStatuses,
      });
    }

    const updatedTicket = await ticketModel.updateTicketStatus(id, status);

    res.json({
      message: 'Estado del ticket actualizado correctamente',
      data: updatedTicket,
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al actualizar el estado del ticket',
      error: error.message,
    });
  }
};

const deleteTicket = async (req, res) => {
  try {
    const { id } = req.params;

    const existingTicket = await ticketModel.getTicketById(id);

    if (!existingTicket) {
      return res.status(404).json({
        message: 'Ticket no encontrado',
      });
    }

    await ticketModel.deleteTicket(id);

    res.json({
      message: 'Ticket eliminado correctamente',
    });
  } catch (error) {
    res.status(500).json({
      message: 'Error al eliminar el ticket',
      error: error.message,
    });
  }
};

module.exports = {
  getAllTickets,
  getTicketById,
  createTicket,
  updateTicket,
  updateTicketStatus,
  deleteTicket,
};