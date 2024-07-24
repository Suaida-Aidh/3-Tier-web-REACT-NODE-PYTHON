import { useEffect, useState } from 'react';
import axios from 'axios';

const List = () => {
    const [movies, setMovies] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newMovie, setNewMovie] = useState({ title: '', year: '' });
    const [editMovie, setEditMovie] = useState(null);

    useEffect(() => {
        fetchMovies();
        const ws = new WebSocket('ws://localhost:3002/ws');
        ws.onmessage = (event) => {
            const { type, data } = JSON.parse(event.data);
            if (type === 'movie_created') {
                setMovies(prevMovies => [...prevMovies, data]);
            } else if (type === 'movie_deleted') {
                setMovies(prevMovies => prevMovies.filter(movie => movie.id !== data.id));
            } else if (type === 'movie_updated') {
                setMovies(prevMovies => prevMovies.map(movie => movie.id === data.id ? data : movie));
            }
        };

        return () => {
            ws.close();
        };
    }, []);


    const fetchMovies = async () => {
        try {
            const response = await axios.get('http://localhost:3001/api/movies');
            setMovies(response.data);
        } catch (error) {
            console.error('Error fetching movies:', error);
        }
    };

    const handleButtonClick = () => {
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setEditMovie(null);
        setNewMovie({ title: '', year: '' });
    };

    
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setNewMovie({ ...newMovie, [name]: value });
    };

    // const handleAddMovie = async () => {
    //     try {
    //         await axios.post('http://localhost:3001/api/movies', newMovie);
    //         setNewMovie({ title: '', year: '' });
    //         fetchMovies();  // Refresh the movie list after adding a new movie
    //     } catch (error) {
    //         console.error('Error adding movie:', error);
    //     }
    // };

    const handleAddMovie = async () =>{
        
        try{
            const response = await axios.post('http://localhost:3001/api/movies',newMovie)
            console.log('Movie added', response.data)
            setNewMovie({ title: '', year: ''})
        }catch (error){
            console.error('Error adding movie:', error);
        }
    }

    const handleDeleteMovie = async (id) => {
        if (!id) {
            console.error("Movie ID is missing");
            return;
        }
        try {
            await axios.delete(`http://localhost:3001/api/movies/${id}`);
        } catch (error) {
            console.error("Error deleting movie:", error);
        }
    };

    const handleEditMovie = (movie) => {
        setEditMovie(movie);
        setNewMovie({ title: movie.title, year: movie.year });
        setIsModalOpen(true);
    };

    const handleUpdateMovie = async () => {
        if (!editMovie || !editMovie.id) {
            console.log('No movie selected');
            return;
        }
        try {
            await axios.put(`http://localhost:3001/api/movies/${editMovie.id}`, newMovie);
            setEditMovie(null);
            setNewMovie({ title: '', year: '' });
        } catch (error) {
            console.error('Error updating movie:', error);
        }
    };

    // const handleCancelEdit = ()

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <button onClick={handleButtonClick}>Show Movies</button>
            {isModalOpen && (
                <div style={{ position: 'fixed', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', backgroundColor: 'white', padding: '20px', border: '1px solid black' }}>
                    <button onClick={closeModal}>x</button>
                    <h2>Movie List</h2>
                    <ul>
                        {movies.map((movie, index) => (
                            <li key={index}>
                                {index}

                                {movie.title} ({movie.year})
                                <button onClick={() => handleEditMovie(movie)}>Edit</button>
                                {/* <button onClick={() => handleDeleteMovie(movie.id)}>Delete</button> */}
                                <button onClick={() => {
                                    console.log("Deleting movie with ID:", movie.id); // Debugging line
                                        handleDeleteMovie(index);
                                    }}>Delete</button>
                            </li>
                        ))}
                    </ul>
                    <input
                        type="text"
                        name="title"
                        placeholder="Movie Title"
                        value={newMovie.title}
                        onChange={handleInputChange}
                    />
                    <input
                        type="number"
                        name="year"
                        placeholder="Year"
                        value={newMovie.year}
                        onChange={handleInputChange}
                    />
                    {editMovie ? (
                        <>
                            <button onClick={handleUpdateMovie}>Update</button>
                            {/* <button onClick={handleCancelEdit}>Cancel Edit</button> */}
                        </>
                    ) : (
                        <button onClick={handleAddMovie}>Add</button>
                    )}
                </div>
            )}
        </div>
    );
};

export default List;
