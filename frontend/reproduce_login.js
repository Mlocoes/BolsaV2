
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const login = async (username, password) => {
    console.log('Testing login with:', username, password);

    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await axios.post(`${API_BASE_URL}/auth/login`, formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });
        console.log('Success:', response.data);
    } catch (error) {
        console.error('Error:', error.response ? error.response.data : error.message);
    }
};

login('admin', 'admin123');
