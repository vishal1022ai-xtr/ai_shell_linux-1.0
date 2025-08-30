document.getElementById('clickMe').addEventListener('click', () => {
    const output = document.getElementById('output');
    const now = new Date().toLocaleTimeString();
    output.textContent = `Button clicked at ${now}`;
});