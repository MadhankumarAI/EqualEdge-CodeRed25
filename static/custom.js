// Initialize SpeechRecognition
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.continuous = true;
recognition.interimResults = false;

let listening = false; // Track whether voice recognition is active
let fontIndex = 0; // Index to track current font
const fonts = ["Arial", "Courier New", "Georgia", "Times New Roman", "Verdana"]; // Available fonts

let currentFontSize = 16; // Default font size
let currentContrast = 1; // Default contrast value

// Start/Stop listening function
function toggleListening() {
    if (!listening) {
        recognition.start();
        listening = true;
        document.getElementById('status').textContent = "Voice recognition is ON";
        console.log("Voice recognition started...");
    } else {
        recognition.stop();
        listening = false;
        document.getElementById('status').textContent = "Voice recognition is OFF";
        console.log("Voice recognition stopped...");
    }
}

// Keybinding for Shift + C
document.addEventListener('keydown', function (event) {
    if (event.key.toLowerCase() === 'c' && event.shiftKey) { // Check for Shift + C
        toggleListening();
    }
});

// Speech recognition event handlers
recognition.onresult = function (event) {
    const transcript = event.results[event.resultIndex][0].transcript.trim().toLowerCase();
    console.log(`Heard: "${transcript}"`);

    // Handle voice commands
    if (transcript.includes("change font")) {
        changeFont();
    } else if (transcript.includes("increase font size")) {
        changeFontSize(2); // Increase by 2px
    } else if (transcript.includes("decrease font size")) {
        changeFontSize(-2); // Decrease by 2px
    } else if (transcript.includes("increase contrast")) {
        adjustContrast(0.1); // Increase contrast by 0.1
    } else if (transcript.includes("decrease contrast")) {
        adjustContrast(-0.1); // Decrease contrast by 0.1
    } else if (transcript.includes("toggle dropdown")) {
        toggleDropdown("dropdownMenu");
    } else if (transcript.includes("toggle slider")) {
        toggleSlider("slider");
    } else {
        console.log("Command not recognized.");
    }
};

recognition.onerror = function (event) {
    console.error("Speech recognition error:", event.error);
    document.getElementById('status').textContent = "Error in voice recognition. Try again.";
};

// Toggle dropdown
function toggleDropdown(id) {
    const dropdown = document.getElementById(id);
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
    console.log("Toggled dropdown");
}

// Toggle slider
function toggleSlider(id) {
    const slider = document.getElementById(id);
    slider.style.display = slider.style.display === "block" ? "none" : "block";
    console.log("Toggled slider");
}

// Change font family
function changeFont() {
    fontIndex = (fontIndex + 1) % fonts.length; // Cycle through fonts
    setFont(fonts[fontIndex]);
}

// Set font family globally
function setFont(font) {
    document.body.style.fontFamily = `${font}, sans-serif`; // Apply to body
    console.log(`Font changed to: ${font}`);
}

// Change font size
function changeFontSize(delta) {
    currentFontSize += delta; // Increment or decrement font size
    if (currentFontSize < 10) currentFontSize = 10; // Minimum font size
    setFontSize(currentFontSize);
}

// Set font size globally
function setFontSize(size) {
    document.documentElement.style.fontSize = `${size}px`;
    document.getElementById('fontSizeValue').textContent = `${size}px`;
}

// Adjust contrast
function adjustContrast(delta) {
    currentContrast += delta;
    if (currentContrast < 1) currentContrast = 1; // Minimum contrast
    if (currentContrast > 2) currentContrast = 2; // Maximum contrast
    setContrast(currentContrast);
}

// Set contrast globally
function setContrast(value) {
    document.documentElement.style.filter = `contrast(${value})`;
    document.getElementById('contrastValue').textContent = value.toFixed(1); // Display one decimal
    console.log(`Contrast set to: ${value}`);
}