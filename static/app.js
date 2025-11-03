document.addEventListener("DOMContentLoaded", function () {
    const qrForm = document.getElementById("createForm");
    const qrContainer = document.getElementById("qrContainer");
    const errorMessage = document.getElementById("errorMessage");
    const linksContainer = document.getElementById("links-container");
    const addLinkBtn = document.getElementById("add-link-btn");
    
    if (!qrForm) return; // Only run the form logic on index.html

    // --- Dynamic Link Form Management ---
    const addLinkInputPair = (isInitial = false) => {
        const linkPairDiv = document.createElement("div");
        linkPairDiv.classList.add("link-pair");

        // Links are optional now; no required attribute on inputs
        const requiredAttr = '';

        linkPairDiv.innerHTML = `
            <div class="form-group-link">
                <input type="text" name="labels[]" class="link-label" placeholder="Choice Label (e.g., Student Portal)" ${requiredAttr}>
                <input type="url" name="urls[]" class="link-url" placeholder="https://example.com/student-form" ${requiredAttr}>
            </div>
            ${!isInitial ? '<button type="button" class="btn-remove-link" title="Remove Link">X</button>' : ''}
        `;

        linksContainer.appendChild(linkPairDiv);

        // Add event listener to the new remove button (only if it exists)
        const removeBtn = linkPairDiv.querySelector(".btn-remove-link");
        if (removeBtn) {
            removeBtn.addEventListener("click", function () {
                this.parentElement.remove();
            });
        }
    };

    // Add one link pair by default on page load
    // Start with one optional link pair so users can add links if they want
    addLinkInputPair(true);

    addLinkBtn.addEventListener("click", () => addLinkInputPair(false));


    // --- Form Submission via AJAX ---
    qrForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        // Simple loading state
        qrContainer.innerHTML = "<p class='loading-message'>Generating... please wait. This may take a few seconds.</p>";
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
        
        // Disable button
    const submitBtn = qrForm.querySelector(".btn-generate");
        submitBtn.disabled = true;
        submitBtn.textContent = "Generating...";

    let formData = new FormData(qrForm);

        try {
            let response = await fetch("/create", {
                method: "POST",
                body: formData
            });

            let result = await response.json();

            if (result.success) {
                qrContainer.innerHTML = ""; // Clear loading message
                result.qr_paths.forEach(qrPath => {
                    const qrBox = document.createElement("div");
                    qrBox.classList.add("qr-box");

                    // Extract style name from the path for display
                    const filename = qrPath.split('/').pop();
                    const styleName = filename.split('_')[0]; 

                    qrBox.innerHTML = `
                        <img src="${qrPath}" alt="Generated QR Code">
                        <p style="text-transform: capitalize;">${styleName} Style</p>
                        <a href="${qrPath}" download="qr_${styleName}.png" class="btn-download">Download</a>
                    `;
                    qrContainer.appendChild(qrBox);
                });
                
                // Reset form fields but keep links/styles
                qrForm.reset();
                addLinkInputPair(true); // Re-add one link pair if needed
                
            } else {
                qrContainer.innerHTML = "<p>Generation failed. Check the error message above.</p>";
                errorMessage.textContent = result.message || "An unknown error occurred.";
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error("Submission Error:", error);
            qrContainer.innerHTML = "<p>Could not connect to the server.</p>";
            errorMessage.textContent = "Failed to connect to the server. Please check your connection and try again.";
            errorMessage.style.display = 'block';
        } finally {
            // Re-enable button
            submitBtn.disabled = false;
            submitBtn.textContent = "Generate QR Codes";
        }
    });

    
});