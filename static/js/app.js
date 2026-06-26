/**
 * Document Compiler — Frontend Logic
 * 
 * Handles:
 *   - Multiple image upload (sequentially to save memory)
 *   - Thumbnail gallery rendering with custom order numbers
 *   - Remove individual items or clear all (with server-side file deletion)
 *   - Proper naming convention formatting: BRANCH PROJECT REFERENCE_NUMBER
 *   - Orientation toggles (portrait/landscape)
 *   - Live PDF Preview rendering using native browser viewer in an iframe
 *   - PDF compilation request and auto-download
 *   - Accessible states & toast alerts
 * 
 * Vanilla JavaScript.
 */

(function () {
    "use strict";

    // =========================================================================
    // DOM References
    // =========================================================================

    const uploadArea        = document.getElementById("upload-area");
    const fileInput         = document.getElementById("file-input");
    
    const galleryContainer  = document.getElementById("gallery-container");
    const galleryGrid       = document.getElementById("gallery-grid");
    const pageCountText     = document.getElementById("page-count");
    const clearAllBtn       = document.getElementById("clear-all-btn");

    // Naming convention inputs
    const pdfBranchInput    = document.getElementById("pdf-branch-input");
    const pdfProjectInput   = document.getElementById("pdf-project-input");
    const pdfRefInput       = document.getElementById("pdf-ref-input");
    const generatedFilenamePreview = document.getElementById("generated-filename-preview");
    
    const previewPdfBtn     = document.getElementById("preview-pdf-btn");
    const pdfBtn            = document.getElementById("pdf-btn");

    const previewPdfContainer = document.getElementById("preview-pdf-container");
    const pdfPreviewIframe    = document.getElementById("pdf-preview-iframe");
    const closePreviewBtn     = document.getElementById("close-preview-btn");

    const loadingOverlay    = document.getElementById("loading-overlay");
    const loadingText       = document.getElementById("loading-text");
    const loadingSubtext    = document.getElementById("loading-subtext");

    const toastContainer    = document.getElementById("toast-container");

    // Steps & Badges
    const stepUpload        = document.getElementById("step-upload");
    const stepReview        = document.getElementById("step-review");
    const stepPdf           = document.getElementById("step-pdf");
    const uploadBadge       = document.getElementById("upload-badge");
    const reviewBadge       = document.getElementById("review-badge");
    const pdfBadge          = document.getElementById("pdf-badge");

    // =========================================================================
    // State Tracker
    // =========================================================================

    let uploadedImages = [];
    let currentPreviewUrl = null;

    // =========================================================================
    // Upload Handlers — Click & Drag-Drop
    // =========================================================================

    uploadArea.addEventListener("click", function () {
        fileInput.click();
    });

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            handleMultipleFiles(fileInput.files);
        }
    });

    uploadArea.addEventListener("dragover", function (e) {
        e.preventDefault();
        uploadArea.classList.add("drag-over");
    });

    uploadArea.addEventListener("dragleave", function () {
        uploadArea.classList.remove("drag-over");
    });

    uploadArea.addEventListener("drop", function (e) {
        e.preventDefault();
        uploadArea.classList.remove("drag-over");

        if (e.dataTransfer.files.length > 0) {
            handleMultipleFiles(e.dataTransfer.files);
        }
    });

    // =========================================================================
    // Upload Queue Management
    // =========================================================================

    async function handleMultipleFiles(filesList) {
        const validFiles = [];
        const allowedTypes = ["image/jpeg", "image/jpg", "image/png"];

        for (let i = 0; i < filesList.length; i++) {
            const file = filesList[i];
            if (!allowedTypes.includes(file.type)) {
                showToast(`Skipped "${file.name}": only JPG, JPEG, and PNG are allowed.`, "warning");
                continue;
            }
            if (file.size > 10 * 1024 * 1024) {
                showToast(`Skipped "${file.name}": File size exceeds the 10 MB limit.`, "warning");
                continue;
            }
            validFiles.push(file);
        }

        if (validFiles.length === 0) return;

        showLoading("Uploading files...", `Processing 1 of ${validFiles.length} images`);

        hidePreview(); // Close preview since elements changed

        for (let idx = 0; idx < validFiles.length; idx++) {
            const file = validFiles[idx];
            loadingSubtext.textContent = `Uploading "${file.name}" (${idx + 1} of ${validFiles.length})`;
            
            try {
                const result = await uploadSingleFile(file);
                uploadedImages.push({
                    filename: result.filename,
                    previewUrl: result.preview_url,
                    originalName: file.name
                });

                // Auto-fill the naming fields if they are currently empty
                if (result.branch && !pdfBranchInput.value.trim()) {
                    pdfBranchInput.value = result.branch.toUpperCase();
                }
                if (result.project && !pdfProjectInput.value.trim()) {
                    pdfProjectInput.value = result.project.toUpperCase();
                }
                if (result.reference && !pdfRefInput.value.trim()) {
                    pdfRefInput.value = result.reference.toUpperCase();
                }
            } catch (err) {
                showToast(`Failed to upload "${file.name}": ${err.message}`, "error");
            }
        }

        hideLoading();
        fileInput.value = "";
        
        renderGallery();
        updateStepStates();
        showToast("Images uploaded successfully!", "success");
    }

    function uploadSingleFile(file) {
        return new Promise(function (resolve, reject) {
            const formData = new FormData();
            formData.append("image", file);

            fetch("/upload", {
                method: "POST",
                body: formData
            })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, status: response.status, data: data };
                });
            })
            .then(function (res) {
                if (res.ok) {
                    resolve(res.data);
                } else {
                    reject(new Error(res.data.error || `Server returned status ${res.status}`));
                }
            })
            .catch(function (err) {
                reject(err);
            });
        });
    }

    // =========================================================================
    // Gallery Rendering & Arrangement
    // =========================================================================

    function renderGallery() {
        galleryGrid.innerHTML = "";

        if (uploadedImages.length === 0) {
            galleryContainer.classList.remove("visible");
            return;
        }

        uploadedImages.forEach(function (img, index) {
            const item = document.createElement("div");
            item.className = "gallery-item";

            const badge = document.createElement("div");
            badge.className = "gallery-item-badge";
            badge.textContent = `Page ${index + 1}`;

            const removeBtn = document.createElement("button");
            removeBtn.className = "remove-item-btn";
            removeBtn.innerHTML = "✕";
            removeBtn.title = "Remove this page";
            removeBtn.addEventListener("click", function () {
                removeImage(index);
            });

            const wrapper = document.createElement("div");
            wrapper.className = "gallery-image-wrapper";

            const elImg = document.createElement("img");
            elImg.className = "gallery-image";
            elImg.src = img.previewUrl;
            elImg.alt = img.originalName;

            wrapper.appendChild(elImg);

            // Re-order controls
            const controls = document.createElement("div");
            controls.className = "gallery-item-controls";

            const moveLeftBtn = document.createElement("button");
            moveLeftBtn.className = "move-page-btn";
            moveLeftBtn.innerHTML = "◀";
            moveLeftBtn.title = "Move page earlier (left)";
            if (index === 0) {
                moveLeftBtn.disabled = true;
            }
            moveLeftBtn.addEventListener("click", function () {
                swapImages(index, index - 1);
            });

            const moveRightBtn = document.createElement("button");
            moveRightBtn.className = "move-page-btn";
            moveRightBtn.innerHTML = "▶";
            moveRightBtn.title = "Move page later (right)";
            if (index === uploadedImages.length - 1) {
                moveRightBtn.disabled = true;
            }
            moveRightBtn.addEventListener("click", function () {
                swapImages(index, index + 1);
            });

            controls.appendChild(moveLeftBtn);
            controls.appendChild(moveRightBtn);

            const label = document.createElement("div");
            label.className = "gallery-item-name";
            label.textContent = img.originalName;

            item.appendChild(badge);
            item.appendChild(removeBtn);
            item.appendChild(wrapper);
            item.appendChild(controls);
            item.appendChild(label);

            galleryGrid.appendChild(item);
        });

        const total = uploadedImages.length;
        pageCountText.textContent = `${total} page${total !== 1 ? "s" : ""} uploaded`;
        galleryContainer.classList.add("visible");
    }

    function swapImages(index1, index2) {
        if (index1 < 0 || index1 >= uploadedImages.length || index2 < 0 || index2 >= uploadedImages.length) {
            return;
        }
        const temp = uploadedImages[index1];
        uploadedImages[index1] = uploadedImages[index2];
        uploadedImages[index2] = temp;
        
        hidePreview();
        renderGallery();
        showToast(`Moved page ${index1 + 1} to position ${index2 + 1}`, "info");
    }

    function removeImage(index) {
        const deletedImg = uploadedImages[index];
        uploadedImages.splice(index, 1);

        hidePreview();

        fetch("/delete-images", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filenames: [deletedImg.filename] })
        });

        renderGallery();
        updateStepStates();
        showToast("Page removed.", "info");
    }

    clearAllBtn.addEventListener("click", function () {
        hidePreview();

        const filenames = uploadedImages.map(function (img) {
            return img.filename;
        });

        fetch("/delete-images", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filenames: filenames })
        });

        uploadedImages = [];
        renderGallery();
        updateStepStates();
        showToast("All pages cleared.", "info");
    });

    // =========================================================================
    // Naming Convention Logic
    // =========================================================================

    function getFormattedFilename() {
        const branch = pdfBranchInput.value.trim().toUpperCase();
        const project = pdfProjectInput.value.trim().toUpperCase();
        const ref = pdfRefInput.value.trim().toUpperCase();

        if (!branch && !project && !ref) {
            return "";
        }

        const parts = [];
        if (branch) parts.push(branch);
        if (project) parts.push(project);
        if (ref) parts.push(ref);

        const combined = parts.join(" ");
        return combined;
    }

    function updateGeneratedFilename() {
        const filename = getFormattedFilename();
        const displayFilename = filename || "compiled_document";
        
        generatedFilenamePreview.textContent = displayFilename + ".pdf";
        if (filename) {
            generatedFilenamePreview.style.color = "var(--color-primary-dark)";
        } else {
            generatedFilenamePreview.style.color = "var(--color-text-secondary)";
        }
        
        // Enable compile buttons if we have images
        if (uploadedImages.length > 0) {
            previewPdfBtn.disabled = false;
            pdfBtn.disabled = false;
        } else {
            previewPdfBtn.disabled = true;
            pdfBtn.disabled = true;
        }
    }

    // Bind event listeners to naming fields
    [pdfBranchInput, pdfProjectInput, pdfRefInput].forEach(function (input) {
        input.addEventListener("input", function () {
            // Automatically make lowercase input appear uppercase for elderly UX
            input.value = input.value.toUpperCase();
            updateGeneratedFilename();
        });
    });

    // =========================================================================
    // Step State Refresh
    // =========================================================================

    function updateStepStates() {
        const hasImages = uploadedImages.length > 0;

        if (hasImages) {
            uploadBadge.classList.add("visible");
            stepReview.classList.remove("disabled");
            reviewBadge.classList.add("visible");
            
            // Re-verify naming inputs to enable buttons
            updateGeneratedFilename();
        } else {
            uploadBadge.classList.remove("visible");
            stepReview.classList.add("disabled");
            reviewBadge.classList.remove("visible");
            
            previewPdfBtn.disabled = true;
            pdfBtn.disabled = true;
            pdfBadge.classList.remove("visible");
        }
    }

    // =========================================================================
    // PDF Compilation & Preview logic
    // =========================================================================

    function fetchPdfBlob() {
        const safeName = getFormattedFilename() || "compiled_document";
        const orientationElement = document.querySelector('input[name="orientation"]:checked');
        const orientation = orientationElement ? orientationElement.value : "portrait";

        const filenamesList = uploadedImages.map(function (img) {
            return img.filename;
        });

        return fetch("/generate-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filenames: filenamesList,
                pdf_name: safeName,
                orientation: orientation
            })
        })
        .then(function (response) {
            if (!response.ok) {
                return response.json().then(function (data) {
                    throw new Error(data.error || "Failed to generate PDF.");
                });
            }

            const disposition = response.headers.get("Content-Disposition");
            let downloadFilename = safeName + ".pdf";
            if (disposition && disposition.indexOf("filename=") !== -1) {
                const match = disposition.match(/filename=([^;]+)/);
                if (match) {
                    downloadFilename = match[1].replace(/"/g, "").trim();
                }
            }

            return response.blob().then(function (blob) {
                return { blob: blob, filename: downloadFilename };
            });
        });
    }

    // --- Action: Download PDF ---
    pdfBtn.addEventListener("click", function () {
        if (uploadedImages.length === 0) {
            showToast("Please upload at least one image to create a PDF.", "warning");
            return;
        }

        showLoading("Generating PDF...", "Compiling your pages. Please wait.");
        pdfBtn.disabled = true;
        previewPdfBtn.disabled = true;

        fetchPdfBlob()
        .then(function (res) {
            hideLoading();

            const url = window.URL.createObjectURL(res.blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = res.filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            pdfBtn.disabled = false;
            previewPdfBtn.disabled = false;
            pdfBadge.classList.add("visible");
            showToast("PDF downloaded successfully!", "success");
        })
        .catch(function (err) {
            hideLoading();
            pdfBtn.disabled = false;
            previewPdfBtn.disabled = false;
            showToast(err.message || "Failed to download PDF.", "error");
            console.error("PDF download error:", err);
        });
    });

    // --- Action: Preview PDF ---
    previewPdfBtn.addEventListener("click", function () {
        if (uploadedImages.length === 0) {
            showToast("Please upload at least one image to preview the PDF.", "warning");
            return;
        }

        hidePreview();

        showLoading("Generating Live Preview...", "Compiling PDF document. Please wait.");
        pdfBtn.disabled = true;
        previewPdfBtn.disabled = true;

        fetchPdfBlob()
        .then(function (res) {
            hideLoading();

            currentPreviewUrl = window.URL.createObjectURL(res.blob);
            pdfPreviewIframe.src = currentPreviewUrl;
            previewPdfContainer.classList.add("visible");

            pdfBtn.disabled = false;
            previewPdfBtn.disabled = false;
            showToast("Preview loaded!", "success");

            previewPdfContainer.scrollIntoView({ behavior: "smooth", block: "start" });
        })
        .catch(function (err) {
            hideLoading();
            pdfBtn.disabled = false;
            previewPdfBtn.disabled = false;
            showToast(err.message || "Failed to generate preview.", "error");
            console.error("PDF preview error:", err);
        });
    });

    // --- Action: Close Preview Panel ---
    closePreviewBtn.addEventListener("click", function () {
        hidePreview();
        showToast("Preview closed.", "info");
    });

    function hidePreview() {
        previewPdfContainer.classList.remove("visible");
        pdfPreviewIframe.src = "";
        if (currentPreviewUrl) {
            window.URL.revokeObjectURL(currentPreviewUrl);
            currentPreviewUrl = null;
        }
    }

    // =========================================================================
    // Common Helpers (Toasts / Loading UI)
    // =========================================================================

    function showLoading(text, subtext) {
        loadingText.textContent = text || "Processing...";
        loadingSubtext.textContent = subtext || "Please wait";
        loadingOverlay.classList.add("visible");
    }

    function hideLoading() {
        loadingOverlay.classList.remove("visible");
    }

    function showToast(message, type) {
        type = type || "success";

        const icons = {
            success: "✅",
            error: "❌",
            warning: "⚠️",
            info: "ℹ️"
        };

        const toast = document.createElement("div");
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || ""}</span>
            <span>${escapeHtml(message)}</span>
        `;

        toast.addEventListener("click", function () {
            dismissToast(toast);
        });

        toastContainer.appendChild(toast);

        setTimeout(function () {
            dismissToast(toast);
        }, 5000);
    }

    function dismissToast(toast) {
        if (!toast || !toast.parentNode) return;
        toast.classList.add("fade-out");
        setTimeout(function () {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }

})();
