const express = require('express');
const axios = require('axios');
const cors = require('cors');
const WebSocket = require('ws');

const app = express();
const port = 3001;

app.use(cors());
app.use(express.json());

const wsServer = new WebSocket.Server({ port: 3002 });

wsServer.on('connection', (socket) => {
    console.log('WebSocket client connected');
    socket.on('message', (message) => {
        console.log('Received:', message);
    });

    socket.on('close', () => {
        console.log('WebSocket client disconnected');
    });
});

app.get('/api/movies', async (req, res) => {
    try {
        const response = await axios.get('http://localhost:8000/movies');
        console.log(response.data)
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch movies' });
    }
});

app.post('/api/movies', async (req, res) => {
    try {
        const response = await axios.post('http://localhost:8000/movies', req.body);
        wsServer.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify({ type: 'movie_created', data: response.data }));
            }
        });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to create movie' });
    }
});



app.delete('/api/movies/:id', async (req, res) => {
    const { id } = req.params;
    try {
        const response = await axios.delete(`http://localhost:8000/movies/${id}`);
        if (response.status === 204) {
            console.log('Movie not found');
            return res.status(204).json({ error: 'Movie not found' });
        }

        wsServer.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(JSON.stringify({ type: 'movie_deleted', data: response.data }));
            }
        });
        res.json(response.data);
    } catch (error) {
        console.error("Error in Node.js server delete:", error);
        res.status(500).json({ error: 'Failed to delete movie' });
    }
});




app.put('/api/movies/:id', async (req, res) => {
    try {
        const response = await axios.put(`http://localhost:8000/movies/${req.params.id}`, req.body);
        res.json(response.data);
    } catch (error) {
        res.status(501).json({ error: 'Failed to update movie' });
    }
});

app.listen(port, () => {
    console.log(`Node.js server listening at http://localhost:${port}`);
});