let accessToken = localStorage.getItem('access_token');
let chartInstance = null;
// Open WebSocket connection
let websocket = null;
let port = 8005;
let host = 'localhost';

function showRegister() {
    document.getElementById("login-section").style.display = "none";
    document.getElementById("register-section").style.display = "block";
}

function showLogin() {
    document.getElementById("register-section").style.display = "none";
    document.getElementById("login-section").style.display = "block";
}
  

// WebSocket with token sent in the message after handshake
function openWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'; // Use wss if HTTPS, ws if HTTP
    const wsHost = window.location.hostname || host; // Get hostname dynamically, default to 'localhost'
    const wsUrl = `${wsProtocol}//${wsHost}:${port}/ws?token=${accessToken}`;
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log("WebSocket connection established.");
    };

    websocket.onmessage = (event) => {
            console.log("Message received from server:", event.data);
    }

    websocket.onerror = (error) => {
        console.error("WebSocket error:", error);
        appendMessage("Bot", "An error occurred while connecting. Please try again later.");
    };

    websocket.onclose = () => {
        console.log("WebSocket connection closed");
    };
}

async function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    if (!email || !password) {
        alert("Please enter email and password");
        return;
    }

    try {
        const response = await fetch(`http://${host}:${port}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username: email, password: password })
        });

        if (!response.ok) throw new Error("Invalid credentials");

        const data = await response.json();
        accessToken = data.access_token;
        
        localStorage.setItem('access_token', accessToken);
        document.getElementById("login-section").style.display = "none";
        document.getElementById("chat-section").style.display = "block";
        openWebSocket();
    } catch (error) {
        alert("Login failed: " + error.message);
    }
}

async function register() {
    const username = document.getElementById("register-username").value;
    const email = document.getElementById("register-email").value;
    const password = document.getElementById("register-password").value;

    if (!username || !email || !password) {
        alert("Please enter all required fields.");
        return;
    }

    try {
        const response = await fetch(`http://${host}:${port}/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, email, password })
        });

        if (!response.ok) throw new Error("Registration failed");

        alert("Registration successful. Please login.");
        showLogin();
    } catch (error) {
        alert("Registration failed: " + error.message);
    }
}



async function sendMessage() {
    const userMessage = document.getElementById("user-message").value.trim();
    if (!userMessage || !accessToken) return;

    appendMessage("You", userMessage);
    document.getElementById("user-message").value = "";

    try {
        // Sending the message via WebSocket
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify({ query: userMessage }));
        }

        const questions_response = await fetch(`http://${host}:${port}/business_questions/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`, // Correct Authorization format
            },
            body: JSON.stringify({ query: userMessage })
        });
        const questions = await questions_response.json();

        const sql_response = await fetch(`http://${host}:${port}/execute_query/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`, // Correct Authorization format
            },
            body: JSON.stringify({ query: userMessage })
        });
        const data = await sql_response.json();

        const description_response = await fetch(`http://${host}:${port}/chart_description/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`, // Correct Authorization format
            },
            body: JSON.stringify({ query: userMessage, data: data.data })
        });
        const description = await description_response.json();

        console.log("userMessage:", userMessage);
        console.log("data:", data.data);
        console.log("description:", description.description);
        console.log("questions:", questions.questions);

        appendMessage("Bot", `Here are the results: ${description.description}`);

        displayTable(data.data);
        displayChart(data.data);
    } catch (error) {
        appendMessage("Bot", "Error fetching results.");
    }
}



function appendMessage(sender, message) {
    const chatBox = document.getElementById("chat-box");
    const messageElement = document.createElement("div");
    messageElement.textContent = `${sender}: ${message}`; // Corrected with backticks
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function displayTable(data) {
    const table = document.getElementById("result-table");
    table.innerHTML = "";
    table.style.display = "table";

    if (data.length === 0) return;

    const headerRow = document.createElement("tr");
    Object.keys(data[0]).forEach(key => {
        const th = document.createElement("th");
        th.textContent = key;
        headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    data.forEach(row => {
        const tr = document.createElement("tr");
        Object.values(row).forEach(value => {
            const td = document.createElement("td");
            td.textContent = value;
            tr.appendChild(td);
        });
        table.appendChild(tr);
    });
}

function displayChart(data) {
    if (!data.length) return;

    const labels = data.map(row => row[Object.keys(row)[0]]);
    const values = data.map(row => row[Object.keys(row)[1]]);
    const ctx = document.getElementById("result-chart").getContext("2d");
    document.getElementById("result-chart").style.display = "block";

    if (chartInstance) {
        chartInstance.destroy(); // Clear previous chart
    }

    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Query Results",
                data: values,
                backgroundColor: "#007bff"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}


async function fetchQuestions() {
    try {
        const response = await fetch(`http://${host}:${port}/business_questions/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${accessToken}`,
            },
            body: JSON.stringify({ query: "Generate business questions" })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        const questions = data.questions;

        const questionsList = document.getElementById("questions-list");
        questionsList.innerHTML = "";  // Clear previous results
        
        questions.forEach((question) => {
            const li = document.createElement("li");
            li.textContent = question;
            questionsList.appendChild(li);
        });

    } catch (error) {
        console.error("Error fetching questions:", error);
    }
}








