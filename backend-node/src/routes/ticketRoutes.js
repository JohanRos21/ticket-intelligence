const express = require('express');
const ticketController = require('../controllers/ticketController');

const router = express.Router();

router.get('/', ticketController.getAllTickets);

router.get('/:id', ticketController.getTicketById);

router.post('/', ticketController.createTicket);

router.put('/:id', ticketController.updateTicket);

router.patch('/:id/status', ticketController.updateTicketStatus);

router.delete('/:id', ticketController.deleteTicket);

module.exports = router;