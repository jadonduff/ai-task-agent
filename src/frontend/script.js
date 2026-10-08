/*
script.js
Owner    : Jadon Duff
Authors  : Jadon Duff, ChatGPT
Date     : 2026-10-08
Version  : v0.0.1
Project  : AI Task Agent
Software : JavaScript

Used For : Frontend logic for the AI Task Agent.

References: None.
*/

const form = document.getElementById("prompt-form");
const promptInput = document.getElementById("prompt");
const output = document.getElementById("output");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    output.textContent = "Thinking...";

    const response = await fetch("/prompt", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            prompt: promptInput.value
        })
    });

    output.textContent = await response.text();
});
