const axios = require('axios');

const manualData = {
    data: [
        { Column1: "Test1", Column2: "Test2", Column3: "Test3" },
        { Column1: "Test4", Column2: "Test5", Column3: "Test6" }
    ],
    dtypes: {
        Column1: "text",
        Column2: "text",
        Column3: "text"
    }
};

axios.post('http://127.0.0.1:5001/manual_input', manualData)
    .then(response => {
        console.log('Manual data submitted successfully:', response.data);
    })
    .catch(error => {
        console.error('Error submitting manual data:', error);
    });
