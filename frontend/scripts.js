// Base URL for your Flask backend API
const BASE_URL = 'https://ai-driven-website-builder.onrender.com';

// --- JWT Handling Functions ---

/**
* Retrieves the JWT access token from localStorage.
* @returns {string|null} The access token or null if not found.
*/
function getToken() {
    return localStorage.getItem('access_token');
}

/**
* Stores the JWT access token in localStorage.
* @param {string} token - The JWT access token to store.
*/
function setToken(token) {
    localStorage.setItem('access_token', token);
}

/**
* Removes the JWT access token from localStorage.
*/
function clearToken() {
    localStorage.removeItem('access_token');
}

/**
* Decodes the JWT token to extract the user's role.
* @param {string} token - The JWT access token.
* @returns {string|null} The user's role (e.g., 'Admin', 'Editor', 'Viewer') or null if decoding fails.
*/
function getUserRoleFromToken(token) {
    try {
        // JWTs are base64 encoded. The payload is the second part (index 1).
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Assuming 'user' is the claim, and it contains 'role' and 'id'
        return payload.user.role; // Access role from the 'user' object
    } catch (e) {
        console.error("Error parsing JWT token for role:", e);
        return null;
    }
}

/**
* Decodes the JWT token to extract the user's ID.
* @param {string} token - The JWT access token.
* @returns {string|null} The user's ID or null if decoding fails.
*/
function getUserIdFromToken(token) {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        // Assuming 'user' is the claim, and it contains 'role' and 'id'
        return payload.user.id; // Access ID from the 'user' object
    } catch (e) {
        console.error("Error parsing JWT token for user ID:", e);
        return null;
    }
}

// --- Generic API Request Helper ---

/**
* Makes an authenticated API request.
* @param {string} url - The API endpoint URL.
* @param {string} method - HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
* @param {object|null} body - JSON body for POST/PUT requests.
* @param {boolean} requiresAuth - True if the request needs a JWT token.
* @returns {Promise<object>} An object containing success status, message, and data.
*/
async function apiRequest(url, method, body = null, requiresAuth = true) {
    const headers = {
        'Content-Type': 'application/json',
    };

    if (requiresAuth) {
        const token = getToken();
        if (!token) {
            return { success: false, message: 'Authentication required. Please log in.' };
        }
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const options = { method, headers };
        if (body) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);
        const data = await response.json();

        if (response.ok) {
            return { success: true, message: data.msg || 'Success', data: data };
        } else {
            // Handle specific JWT errors from backend if they are not caught by Flask-JWT Extended's default handlers
            if (response.status === 401 || response.status === 403) {
                if (data.msg && (data.msg.includes('expired') || data.msg.includes('invalid') || data.msg.includes('Missing Authorization'))) {
                    clearToken();
                    // Use a custom message box instead of alert()
                    const messageBox = document.createElement('div');
                    messageBox.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background-color: #f44336; color: white; padding: 15px; border-radius: 5px; z-index: 1000;';
                    messageBox.textContent = "Your session has expired or is invalid. Please log in again.";
                    document.body.appendChild(messageBox);
                    setTimeout(() => {
                        document.body.removeChild(messageBox);
                        window.location.href = 'login.html';
                    }, 3000); // Show for 3 seconds before redirect
                }
            }
            return { success: false, message: data.msg || `API Error: ${response.statusText}` };
        }
    } catch (error) {
        console.error(`API Request Error (${method} ${url}):`, error);
        return { success: false, message: 'Network error or server unreachable. Please check your connection and ensure the backend server is running.' };
    }
}

// --- Authentication API Calls ---

/**
* Calls the signup API.
* @param {string} email - User's email.
* @param {string} password - User's password.
* @returns {Promise<object>} Signup response.
*/
async function signup(email, password) {
    return apiRequest(`${BASE_URL}/auth/signup`, 'POST', { email, password }, false); // No auth required for signup
}

/**
* Calls the login API and stores the token.
* @param {string} email - User's email.
* @param {string} password - User's password.
* @returns {Promise<object>} Login response.
*/
async function login(email, password) {
    const response = await apiRequest(`${BASE_URL}/auth/login`, 'POST', { email, password }, false); // No auth required for login
    if (response.success && response.data.access_token) {
        setToken(response.data.access_token);
    }
    return response;
}

// --- Website Management API Calls ---

/**
* Generates a new website.
* @param {string} business_type - Type of business.
* @param {string} industry - Industry of the business.
* @returns {Promise<object>} Website generation response.
*/
async function generateWebsite(business_type, industry) {
    return apiRequest(`${BASE_URL}/api/generate`, 'POST', { business_type, industry });
}

/**
* Fetches a list of websites.
* @returns {Promise<object>} List of websites.
*/
async function getWebsites() {
    // Note: The backend's /api/ route returns a list directly, not nested under 'data' or 'websites'
    const response = await apiRequest(`${BASE_URL}/api/`, 'GET');
    if (response.success) {
        return { success: true, websites: response.data }; // Assume response.data is the array of websites
    }
    return response;
}

/**
* Fetches a single website by ID.
* @param {string} id - Website ID.
* @returns {Promise<object>} Single website data.
*/
async function getWebsiteById(id) {
    const response = await apiRequest(`${BASE_URL}/api/${id}`, 'GET');
    if (response.success) {
        return { success: true, website: response.data };
    }
    return response;
}

/**
* Updates a website by ID.
* @param {string} id - Website ID.
* @param {object} updateData - Data to update (e.g., { content: { title: "New Title" } }).
* @returns {Promise<object>} Update response.
*/
async function updateWebsite(id, updateData) {
    return apiRequest(`${BASE_URL}/api/${id}`, 'PUT', updateData);
}

/**
* Deletes a website by ID.
* @param {string} id - Website ID.
* @returns {Promise<object>} Delete response.
*/
async function deleteWebsite(id) {
    return apiRequest(`${BASE_URL}/api/${id}`, 'DELETE');
}

// --- Admin API Calls ---

/**
* Assigns a new role to a user.
* @param {string} userId - ID of the user to modify.
* @param {string} role - New role (Admin, Editor, Viewer).
* @returns {Promise<object>} Role assignment response.
*/
async function assignRole(userId, role) {
    return apiRequest(`${BASE_URL}/admin/assign-role`, 'PUT', { user_id: userId, role: role });
}

/**
* Lists all users.
* @returns {Promise<object>} List of users.
*/
async function listUsers() {
    const response = await apiRequest(`${BASE_URL}/admin/users`, 'GET');
    if (response.success) {
        return { success: true, users: response.data }; // Assume response.data is the array of users
    }
    return response;
}

/**
* Deletes a user by ID.
* @param {string} userId - ID of the user to delete.
* @returns {Promise<object>} Delete user response.
*/
async function deleteUser(userId) {
    return apiRequest(`${BASE_URL}/admin/users/${userId}`, 'DELETE');
}

// --- New Modal Functions for Editing Website Content (GLOBAL SCOPE) ---
function openEditWebsiteModal(siteId) {
    const modal = document.getElementById('editWebsiteModal');
    const editWebsiteId = document.getElementById('editWebsiteId');
    const editTitle = document.getElementById('editTitle');
    const editHeroHeading = document.getElementById('editHeroHeading');
    const editHeroSubheading = document.getElementById('editHeroSubheading');
    const editAboutHeading = document.getElementById('editAboutHeading');
    const editAboutText = document.getElementById('editAboutText');
    const editContactEmail = document.getElementById('editContactEmail');
    const editContactPhone = document.getElementById('editContactPhone');
    const editContactAddress = document.getElementById('editContactAddress');
    const editWebsiteMessage = document.getElementById('editWebsiteMessage');

    editWebsiteMessage.textContent = ''; // Clear previous messages
    editWebsiteMessage.className = 'message';

    // Fetch the full website data to populate the form
    getWebsiteById(siteId).then(response => {
        if (response.success && response.website && response.website.content) {
            const content = response.website.content;
            editWebsiteId.value = siteId;
            editTitle.value = content.title || '';
            
            // Populate Hero Section
            editHeroHeading.value = content.hero_section?.heading || '';
            editHeroSubheading.value = content.hero_section?.subheading || '';

            // Populate About Section
            editAboutHeading.value = content.about_section?.heading || '';
            editAboutText.value = content.about_section?.text || '';

            // Populate Contact Section
            editContactEmail.value = content.contact_section?.email || '';
            editContactPhone.value = content.contact_section?.phone || '';
            editContactAddress.value = content.contact_section?.address || '';

            modal.style.display = 'block'; // Show the modal
        } else {
            showMessageBox('Failed to load website data for editing: ' + response.message, 'error');
        }
    });
}

function closeEditWebsiteModal() {
    document.getElementById('editWebsiteModal').style.display = 'none';
    document.getElementById('editWebsiteForm').reset(); // Clear form fields
}

// --- Custom Message Box (instead of alert/confirm) (GLOBAL SCOPE) ---
function showMessageBox(message, type = 'info', duration = 3000) {
    const messageBox = document.createElement('div');
    messageBox.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background-color: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#2196F3'};
        color: white;
        padding: 15px 25px;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease-in-out;
        font-weight: 500;
    `;
    messageBox.textContent = message;
    document.body.appendChild(messageBox);

    // Fade in
    setTimeout(() => { messageBox.style.opacity = '1'; }, 10);

    // Fade out and remove
    setTimeout(() => {
        messageBox.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(messageBox)) {
                document.body.removeChild(messageBox);
            }
        }, 300);
    }, duration);
}

function showConfirmBox(message) {
    return new Promise((resolve) => {
        const confirmBox = document.createElement('div');
        confirmBox.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background-color: #ffffff;
            color: #333;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            z-index: 10001;
            text-align: center;
            max-width: 400px;
        `;
        confirmBox.innerHTML = `
            <p style="margin-bottom: 20px; font-size: 1.1em;">${message}</p>
            <button id="confirmYes" style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin-right: 10px;">Yes</button>
            <button id="confirmNo" style="background-color: #f44336; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">No</button>
        `;
        document.body.appendChild(confirmBox);

        document.getElementById('confirmYes').onclick = () => {
            document.body.removeChild(confirmBox);
            resolve(true);
        };
        document.getElementById('confirmNo').onclick = () => {
            document.body.removeChild(confirmBox);
            resolve(false);
        };
    });
}

// --- Dashboard Specific Logic (Moved from dashboard.html) ---
document.addEventListener('DOMContentLoaded', async () => {
    const token = getToken();
    const authMessageDiv = document.getElementById('authMessage');
    const adminLink = document.getElementById('adminLink');
    const generateWebsiteSection = document.getElementById('generateWebsiteSection'); // Get the generate section

    // --- DEBUGGING START ---
    console.log("Dashboard loaded (inside DOMContentLoaded in scripts.js).");
    console.log("Token from localStorage:", token);
    // --- DEBUGGING END ---


    if (!token) {
        authMessageDiv.style.display = 'block';
        authMessageDiv.textContent = 'Please log in to access the dashboard.';
        // setTimeout(() => { window.location.href = 'login.html'; }, 1500); // Temporarily commented out for debugging
        return;
    }

    const userRole = getUserRoleFromToken(token);
    // --- DEBUGGING START ---
    console.log("User Role from token:", userRole);
    // --- DEBUGGING END ---

    // Hide/Show Generate Website Section based on role
    if (userRole === 'Viewer') {
        if (generateWebsiteSection) {
            generateWebsiteSection.style.display = 'none';
            console.log("Generate Website section hidden for Viewer role.");
        }
    } else {
        if (generateWebsiteSection) {
            generateWebsiteSection.style.display = 'block'; // Ensure it's visible for Admin/Editor
            console.log("Generate Website section visible for Admin/Editor role.");
        }
    }

    if (userRole === 'Admin') {
        adminLink.style.display = 'inline-flex'; // Show admin link
    } else {
        // --- DEBUGGING START ---
        console.log("User is not Admin. Admin link will remain hidden.");
        // --- DEBUGGING END ---
    }


    // Logout button
    document.getElementById('logoutBtn').addEventListener('click', () => {
        clearToken();
        window.location.href = 'login.html';
    });


    // Generate Website Form
    document.getElementById('generateForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const business_type = document.getElementById('business_type').value;
        const industry = document.getElementById('industry').value;
        const generateMessageDiv = document.getElementById('generateMessage');
        const loader = document.getElementById('loader');

        loader.style.display = 'block';
        generateMessageDiv.textContent = ''; // Clear previous messages
        generateMessageDiv.className = 'message'; // Reset class

        const response = await generateWebsite(business_type, industry);

        loader.style.display = 'none';
        if (response.success) {
            generateMessageDiv.className = 'message success';
            generateMessageDiv.textContent = response.message;
            document.getElementById('business_type').value = ''; // Clear form
            document.getElementById('industry').value = '';
            loadWebsites(); // Reload websites after generation
        } else {
            generateMessageDiv.className = 'message error';
            generateMessageDiv.textContent = response.message;
        }
    });


    // Function to load existing websites
    async function loadWebsites() {
        const websitesContainer = document.getElementById('websitesContainer');
        const websitesMessage = document.getElementById('websitesMessage');
        websitesContainer.innerHTML = ''; // Clear previous list
        websitesMessage.textContent = 'Loading websites...';
        websitesMessage.className = 'message'; // Reset class

        const response = await getWebsites(); // Call from scripts.js

        if (response.success) {
            websitesMessage.textContent = ''; // Clear loading message
            if (response.websites.length === 0) {
                websitesMessage.textContent = 'No websites created yet.';
            } else {
                const currentUserId = getUserIdFromToken(token); // Get current user ID once
                response.websites.forEach(site => {
                    const div = document.createElement('div');
                    div.className = 'website-item';
                    div.innerHTML = `
                        <div class="website-item-details">
                            <strong>${site.business_type || 'N/A'}</strong> in ${site.industry || 'N/A'}
                            (ID: ${site._id})
                        </div>
                        <div class="website-item-actions">
                            <a href="/preview/${site._id}" target="_blank" class="action-btn view">View Preview</a>
                            <button class="action-btn edit" data-id="${site._id}" data-owner="${site.owner_id}" style="display:none;">Edit</button>
                            <button class="action-btn delete" data-id="${site._id}" data-owner="${site.owner_id}" style="display:none;">Delete</button>
                        </div>
                    `;
                    websitesContainer.appendChild(div);

                    // Show/hide edit/delete buttons based on role and ownership
                    const editButton = div.querySelector('.action-btn.edit');
                    const deleteButton = div.querySelector('.action-btn.delete');

                    console.log(`Site ID: ${site._id}, Site Owner: ${site.owner_id}, Current User ID: ${currentUserId}, User Role: ${userRole}`); // DEBUGGING
                    console.log(`Is Admin: ${userRole === 'Admin'}`); // DEBUGGING
                    console.log(`Is Editor and Owns Site: ${userRole === 'Editor' && site.owner_id === currentUserId}`); // DEBUGGING

                    // Editors can edit/delete their own, Admins can edit/delete any
                    if (userRole === 'Admin' || (userRole === 'Editor' && site.owner_id === currentUserId)) {
                        editButton.style.display = 'inline-block';
                        deleteButton.style.display = 'inline-block';
                        console.log(`Buttons shown for site ${site._id}`); // DEBUGGING
                    } else {
                        console.log(`Buttons hidden for site ${site._id}`); // DEBUGGING
                    }
                });

                // Add event listeners for edit/delete buttons
                websitesContainer.querySelectorAll('.action-btn.edit').forEach(button => {
                    button.addEventListener('click', async () => {
                        const siteId = button.dataset.id;
                        openEditWebsiteModal(siteId); // Call the new function to open modal
                    });
                });

                websitesContainer.querySelectorAll('.action-btn.delete').forEach(button => {
                    button.addEventListener('click', async () => {
                        const siteId = button.dataset.id;
                        // Use a custom message box instead of confirm()
                        const confirmDelete = await showConfirmBox('Are you sure you want to delete this website? This action cannot be undone.');
                        if (confirmDelete) {
                            const response = await deleteWebsite(siteId);
                            if (response.success) {
                                showMessageBox('Website deleted successfully!', 'success');
                                loadWebsites(); // Reload list
                            } else {
                                showMessageBox('Failed to delete website: ' + response.message, 'error');
                            }
                        }
                    });
                });
            }
        } else {
            websitesMessage.className = 'message error';
            websitesMessage.textContent = 'Error loading websites: ' + response.message;
        }
    }

    // Handle form submission for editing website
    document.getElementById('editWebsiteForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const siteId = document.getElementById('editWebsiteId').value;
        const editWebsiteMessage = document.getElementById('editWebsiteMessage');

        const updatedContent = {
            title: document.getElementById('editTitle').value,
            hero_section: {
                heading: document.getElementById('editHeroHeading').value,
                subheading: document.getElementById('editHeroSubheading').value,
                // image_description is AI-generated, not directly editable here
                image_description: '' // Placeholder, will be overwritten by existing if not provided
            },
            about_section: {
                heading: document.getElementById('editAboutHeading').value,
                text: document.getElementById('editAboutText').value
            },
            // services_section is not directly editable in this modal
            contact_section: {
                email: document.getElementById('editContactEmail').value,
                phone: document.getElementById('editContactPhone').value,
                address: document.getElementById('editContactAddress').value
            }
        };

        // Fetch existing content to merge, especially for image_description in hero_section
        const existingSiteResponse = await getWebsiteById(siteId);
        if (existingSiteResponse.success && existingSiteResponse.website && existingSiteResponse.website.content) {
            const existingContent = existingSiteResponse.website.content;
            if (existingContent.hero_section && existingContent.hero_section.image_description) {
                updatedContent.hero_section.image_description = existingContent.hero_section.image_description;
            }
            // Merge existing services_section as it's not edited in this modal
            if (existingContent.services_section) {
                updatedContent.services_section = existingContent.services_section;
            }
        } else {
            editWebsiteMessage.className = 'message error';
            editWebsiteMessage.textContent = 'Could not fetch original content for merge. Saving partial update.';
        }


        const response = await updateWebsite(siteId, { content: updatedContent });

        if (response.success) {
            editWebsiteMessage.className = 'message success';
            editWebsiteMessage.textContent = response.message;
            loadWebsites(); // Reload websites list to show changes
            setTimeout(closeEditWebsiteModal, 1500); // Close modal after a short delay
        } else {
            editWebsiteMessage.className = 'message error';
            editWebsiteMessage.textContent = response.message;
        }
    });

    // Initial load of websites
    loadWebsites();
});
