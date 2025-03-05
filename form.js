document.getElementById("submissionForm").addEventListener("submit", async function(event) {
    event.preventDefault(); // Prevent page reload

    let githubLink = document.getElementById("githubLink").value;
    let zipFile = document.getElementById("zipUpload").files[0];
    let formData = new FormData();

    if (githubLink) formData.append("githubLink", githubLink);
    if (zipFile) formData.append("zipFile", zipFile);

    try {
        // Send data to the backend
        let response = await fetch("http://127.0.0.1:5000/submit", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to submit project. Please try again.");
        }

        let result = await response.json();

        // Redirect to the summary page with AI summary in URL
        window.location.href = `summary.html?summary=${encodeURIComponent(result.summary)}`;
    } catch (error) {
        alert("Error: " + error.message);
    }
});