const axios = require('axios');
const fs = require('fs');

const formData = new FormData();
formData.append('file', fs.createReadStream('uploads/sample_data.csv'));

axios.post('http://127.0.0.1:5001/upload', formData, {
    headers: {
        ...formData.getHeaders()
    }
})
.then(response => {
    console.log('File uploaded successfully:', response.data);
})
.catch(error => {
    console.error('Error uploading file:', error);
});
