document.addEventListener('DOMContentLoaded', () => {
    const demos = {};
    const templateIDToLayout = {};

    if (window.DYNAMIC_TEMPLATES && window.DYNAMIC_TEMPLATES.length > 0) {
        window.DYNAMIC_TEMPLATES.forEach(t => {
            if (t.demo) {
                t.demo.templateId = t.templateId;
                t.demo.personal = t.demo.personal || {};
                t.demo.experience = t.demo.experience || [];
                t.demo.education = t.demo.education || [];
                t.demo.projects = t.demo.projects || [];
                t.demo.skills = t.demo.skills || [];
                t.demo.techSkills = t.demo.techSkills || [];
                t.demo.softSkills = t.demo.softSkills || [];
                t.demo.languages = t.demo.languages || [];
                t.demo.achievements = t.demo.achievements || [];
                t.demo.hobbies = t.demo.hobbies || [];
                t.demo.certifications = t.demo.certifications || [];
                t.demo.activities = t.demo.activities || [];
                t.demo.references = t.demo.references || [];
            }
            demos[t.templateId] = t.demo || { 
                templateId: t.templateId, 
                personal: {}, 
                experience: [], 
                education: [], 
                projects: [],
                skills: [],
                techSkills: [],
                softSkills: [],
                languages: [],
                achievements: [],
                hobbies: [],
                certifications: [],
                activities: [],
                references: []
            };
            templateIDToLayout[t.templateId] = t.baseLayout || 'marjorie';
        });
    }

    let activeTemplate = Object.keys(demos)[0];
    let resumeData = demos[activeTemplate] ? JSON.parse(JSON.stringify(demos[activeTemplate])) : null;

    const screens = {
        template: document.getElementById('template-selection'),
        input: document.getElementById('content-input'),
        final: document.getElementById('final-preview')
    };
    const templateCards = document.querySelectorAll('.template-card');
    const previewContainer = document.getElementById('live-preview-container');
    const finalResumeContainer = document.getElementById('final-resume-container');
    const formContainer = document.getElementById('resume-form');

    const updateFormFields = (templateId) => {
        const layout = templateIDToLayout[templateId] || templateId;
        
        let html = `
            <div class="form-section active" data-section="personal">
                <h2>Personal Details</h2>
        `;

        if (layout === 'marjorie' || layout === 'juliana' || layout === 'fresher2') {
            html += `
                <div class="input-group">
                    <label>Profile Photo</label>
                    <input type="file" id="photo-upload" accept="image/*">
                </div>
            `;
        }

        html += `
                <div class="input-group">
                    <label>Full Name</label>
                    <input type="text" id="fullName" value="${resumeData.personal.fullName || ''}">
                </div>
                <div class="input-row">
                    <div class="input-group">
                        <label>Email</label>
                        <input type="email" id="email" value="${resumeData.personal.email || ''}">
                    </div>
                    <div class="input-group">
                        <label>Phone</label>
                        <input type="tel" id="phone" value="${resumeData.personal.phone || ''}">
                    </div>
                </div>
        `;

        if (layout === 'marjorie') {
            html += `
                <div class="input-group">
                    <label>Date of Birth</label>
                    <input type="text" id="dob" value="${resumeData.personal.dob || ''}">
                </div>
            `;
        }

        html += `
                <div class="input-group">
                    <label>Location / Address</label>
                    <input type="text" id="location" value="${resumeData.personal.location || ''}">
                </div>
        `;

        if (layout === 'john' || layout === 'susanne' || layout === 'fresher1' || layout === 'fresher2') {
            html += `
                <div class="input-row">
                    <div class="input-group">
                        <label>LinkedIn</label>
                        <input type="text" id="linkedin" value="${resumeData.personal.linkedin || ''}">
                    </div>
                    <div class="input-group">
                        <label>Twitter / Portfolio URL</label>
                        <input type="text" id="twitter" value="${resumeData.personal.twitter || ''}">
                    </div>
                </div>
            `;
        }

        if (layout === 'john' || layout === 'fresher2') {
            html += `
                <div class="input-group">
                    <label>Professional Title</label>
                    <input type="text" id="professionalTitle" value="${resumeData.personal.professionalTitle || ''}">
                </div>
            `;
        }

        html += `
                <div class="input-row">
                    <div class="input-group">
                        <label>LinkedIn URL</label>
                        <input type="text" id="linkedin" value="${resumeData.personal.linkedin || ''}">
                    </div>
                    <div class="input-group">
                        <label>GitHub URL</label>
                        <input type="text" id="github" value="${resumeData.personal.github || ''}">
                    </div>
                </div>
                <div class="input-group">
                    <label>Objective / Profile Summary</label>
                    <textarea id="summary">${resumeData.personal.summary || ''}</textarea>
                </div>
            </div>
        `;

        if (layout === 'fresher1' || layout === 'fresher2') {
            html += `
                <div class="form-section">
                    <h2>Projects (Fresher Template feature)</h2>
                    <div id="project-list"></div>
                    <button type="button" class="btn btn-outline" id="add-project">+ Add Project</button>
                </div>
            `;
        }

        html += `
            <div class="form-section">
                <h2>Experience / Work History</h2>
                <div id="experience-list"></div>
                <button type="button" class="btn btn-outline" id="add-experience">+ Add Experience</button>
            </div>
            <div class="form-section">
                <h2>Education</h2>
                <div id="education-list"></div>
                <button type="button" class="btn btn-outline" id="add-education">+ Add Education</button>
            </div>
        `;

        html += `
            <div class="form-section">
                <h2>Skills & Expertise</h2>
                <div class="input-group">
                    <label>Technical Skills (comma separated)</label>
                    <input type="text" id="techSkills" value="${(resumeData.techSkills || []).join(', ') || (resumeData.skills || []).join(', ')}">
                </div>
                <div class="input-group">
                    <label>Soft Skills (comma separated)</label>
                    <input type="text" id="softSkills" value="${(resumeData.softSkills || []).join(', ')}">
                </div>
            </div>

            <div class="form-section">
                <h2>Additional Sections</h2>
                <div class="input-group">
                    <label>Languages (comma separated)</label>
                    <input type="text" id="languages" value="${(resumeData.languages || []).join(', ')}">
                </div>
                <div class="input-group">
                    <label>Certifications (one per line)</label>
                    <textarea id="certifications-input" style="min-height: 80px">${(resumeData.certifications || []).join('\n')}</textarea>
                </div>
                <div class="input-group">
                    <label>Achievements (comma separated)</label>
                    <input type="text" id="achievements" value="${(resumeData.achievements || []).join(', ')}">
                </div>
                <div class="input-group">
                    <label>Hobbies (comma separated)</label>
                    <input type="text" id="hobbies" value="${(resumeData.hobbies || []).join(', ')}">
                </div>
            </div>
        `;

        if (layout === 'marjorie' || layout === 'susanne' || layout === 'fresher2') {
            html += `
                <div class="form-section">
                    <h2>Activities / Volunteering</h2>
                    <textarea id="activities-input" style="min-height: 100px">${(resumeData.activities || []).join('\n')}</textarea>
                </div>
            `;
        }
        
        if (layout === 'marjorie') {
            html += `
                <div class="form-section">
                    <h2>References</h2>
                    <textarea id="references-input" style="min-height: 100px">${(resumeData.references || []).join('\n')}</textarea>
                </div>
            `;
        }

        formContainer.innerHTML = html;

        formContainer.querySelectorAll('input, select, textarea').forEach(i => i.addEventListener('input', syncForm));

        const photoInput = document.getElementById('photo-upload');
        if (photoInput) {
            photoInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = (event) => {
                        resumeData.personal.profilePhoto = event.target.result;
                        updatePreview();
                    };
                    reader.readAsDataURL(file);
                }
            });
        }

        document.getElementById('add-experience').addEventListener('click', () => {
            addListItem('experience-list', { role: '', company: '', duration: '', desc: '' }, 'exp');
        });
        document.getElementById('add-education').addEventListener('click', () => {
            addListItem('education-list', { degree: '', school: '', year: '', desc: '' }, 'edu');
        });
        document.getElementById('add-project')?.addEventListener('click', () => {
            addListItem('project-list', { name: '', technologies: '', link: '', desc: '' }, 'proj');
        });

        (resumeData.experience || []).forEach(e => addListItem('experience-list', e, 'exp'));
        (resumeData.education || []).forEach(ed => addListItem('education-list', ed, 'edu'));
        (resumeData.projects || []).forEach(p => addListItem('project-list', p, 'proj'));
    };

    const addListItem = (containerId, data, type) => {
        const div = document.createElement('div');
        div.className = 'experience-item';
        div.innerHTML = `<button class="remove-item">×</button>`;

        if (type === 'exp') {
            div.innerHTML += `
                <input type="text" value="${data.role || ''}" placeholder="Role" class="item-role">
                <input type="text" value="${data.company || ''}" placeholder="Company" class="item-company">
                <input type="text" value="${data.duration || ''}" placeholder="Duration" class="item-duration">
                <textarea class="item-desc" placeholder="Desc">${data.desc || ''}</textarea>
            `;
        } else if (type === 'proj') {
            div.innerHTML += `
                <input type="text" value="${data.name || ''}" placeholder="Project Name" class="item-name">
                <input type="text" value="${data.technologies || ''}" placeholder="Technologies Used" class="item-tech">
                <input type="text" value="${data.link || ''}" placeholder="Link / Year" class="item-link">
                <textarea class="item-desc" placeholder="Project Description">${data.desc || ''}</textarea>
            `;
        }  else {
            div.innerHTML += `
                <input type="text" value="${data.degree || ''}" placeholder="Degree / Major" class="item-degree">
                <input type="text" value="${data.school || ''}" placeholder="School" class="item-school">
                <input type="text" value="${data.year || ''}" placeholder="Year" class="item-year">
                <textarea class="item-desc" placeholder="Additional Details / GPA">${data.desc || ''}</textarea>
            `;
        }

        div.querySelector('.remove-item').addEventListener('click', () => { div.remove(); syncForm(); });
        div.querySelectorAll('input, textarea').forEach(i => i.addEventListener('input', syncForm));
        document.getElementById(containerId).appendChild(div);
    };

    const syncForm = () => {
        resumeData.personal.fullName = document.getElementById('fullName')?.value || '';
        resumeData.personal.email = document.getElementById('email')?.value || '';
        resumeData.personal.phone = document.getElementById('phone')?.value || '';
        resumeData.personal.location = document.getElementById('location')?.value || '';
        resumeData.personal.professionalTitle = document.getElementById('professionalTitle')?.value || '';
        resumeData.personal.summary = document.getElementById('summary')?.value || '';

        if (document.getElementById('dob')) resumeData.personal.dob = document.getElementById('dob').value;
        if (document.getElementById('linkedin')) resumeData.personal.linkedin = document.getElementById('linkedin').value;
        if (document.getElementById('github')) resumeData.personal.github = document.getElementById('github').value;
        if (document.getElementById('twitter')) resumeData.personal.twitter = document.getElementById('twitter').value;

        resumeData.experience = Array.from(document.querySelectorAll('#experience-list .experience-item')).map(i => ({
            role: i.querySelector('.item-role')?.value || '',
            company: i.querySelector('.item-company')?.value || '',
            duration: i.querySelector('.item-duration')?.value || '',
            desc: i.querySelector('.item-desc')?.value || ''
        }));
        resumeData.education = Array.from(document.querySelectorAll('#education-list .experience-item')).map(i => ({
            degree: i.querySelector('.item-degree')?.value || '',
            school: i.querySelector('.item-school')?.value || '',
            year: i.querySelector('.item-year')?.value || '',
            desc: i.querySelector('.item-desc')?.value || ''
        }));
        if (document.getElementById('project-list')) {
            resumeData.projects = Array.from(document.querySelectorAll('#project-list .experience-item')).map(i => ({
                name: i.querySelector('.item-name')?.value || '',
                technologies: i.querySelector('.item-tech')?.value || '',
                link: i.querySelector('.item-link')?.value || '',
                desc: i.querySelector('.item-desc')?.value || ''
            }));
        }

        const getLines = (id) => (document.getElementById(id)?.value || '').split('\n').filter(s => s.trim());
        const getComma = (id) => (document.getElementById(id)?.value || '').split(',').map(s => s.trim()).filter(s => s);

        if (document.getElementById('skills-input')) resumeData.skills = getLines('skills-input');
        if (document.getElementById('techSkills')) resumeData.techSkills = getComma('techSkills');
        if (document.getElementById('softSkills')) resumeData.softSkills = getComma('softSkills');
        if (document.getElementById('languages')) resumeData.languages = getComma('languages');
        if (document.getElementById('achievements')) resumeData.achievements = getComma('achievements');
        if (document.getElementById('hobbies')) resumeData.hobbies = getComma('hobbies');

        if (document.getElementById('activities-input')) resumeData.activities = getLines('activities-input');
        if (document.getElementById('references-input')) resumeData.references = getLines('references-input');
        if (document.getElementById('certifications-input')) resumeData.certifications = getLines('certifications-input');

        if (document.getElementById('software-input')) {
            resumeData.software = getLines('software-input').map(line => {
                const parts = line.split('|');
                return { name: parts[0]?.trim() || '', level: parts[1]?.trim() || '5', label: parts[2]?.trim() || '' };
            });
        }

        updatePreview();
    };

    const renderTemplate = (data) => {
        if (!data) return '<p>No data</p>';
        const personal = data.personal || {};
        const experience = data.experience || [];
        const education = data.education || [];
        const projects = data.projects || [];
        const templateId = data.templateId;
        const layout = templateIDToLayout[templateId] || templateId;

        if (layout === 'fresher1') {
            const h2Style = "font-family: inherit; font-size: 1.25rem; color: #2563eb; margin: 25px 0 15px; font-weight: bold; border-bottom: 2px solid #2563eb; padding-bottom: 5px;";
            return `
                <div class="res-body" style="font-family: 'Inter', Arial, sans-serif; color: #333; font-size: 10pt; line-height: 1.5; padding: 40px; background: #fff;">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <h1 style="font-size: 2.5rem; font-weight: 800; color: #1e3a8a; margin: 0 0 10px 0; text-transform: uppercase;">${personal.fullName}</h1>
                        <div style="font-size: 0.95rem; color: #4b5563; line-height: 1.6;">
                            ${personal.location ? `<span>${personal.location}</span>` : ''}
                            ${personal.phone ? `<span style="margin: 0 8px;">|</span><span>${personal.phone}</span>` : ''}
                            ${personal.email ? `<span style="margin: 0 8px;">|</span><span style="color: #2563eb;">${personal.email}</span>` : ''}
                            ${personal.linkedin ? `<span style="margin: 0 8px;">|</span><span style="color: #2563eb;">${personal.linkedin}</span>` : ''}
                            ${personal.twitter ? `<span style="margin: 0 8px;">|</span><span style="color: #2563eb;">${personal.twitter}</span>` : ''}
                        </div>
                    </div>
                    
                    <p style="margin-bottom: 25px; color: #374151; font-size: 1rem;">${personal.summary}</p>

                    <h2 style="${h2Style}">EDUCATION</h2>
                    <div style="margin-bottom: 20px;">
                        ${education.map(ed => `
                            <div style="margin-bottom: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                    <div style="font-weight: 700; font-size: 1.05rem; color: #1f2937;">${ed.school}</div>
                                    <div style="font-weight: 600; color: #4b5563; font-size: 0.9rem;">${ed.year}</div>
                                </div>
                                <div style="font-style: italic; color: #4b5563; margin-bottom: 3px;">${ed.degree}</div>
                                <div style="white-space: pre-line; color: #4b5563; font-size: 0.95rem; padding-left: 15px; border-left: 2px solid #e5e7eb;">${ed.desc || ''}</div>
                            </div>
                        `).join('')}
                    </div>

                    ${projects.length > 0 ? `
                        <h2 style="${h2Style}">TECHNICAL PROJECTS</h2>
                        <div style="margin-bottom: 20px;">
                            ${projects.map(p => `
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                        <div style="font-weight: 700; font-size: 1.05rem; color: #1f2937;">
                                            ${p.name} <span style="font-weight: 400; font-style: italic; color: #6b7280; font-size: 0.95rem;">| ${p.technologies}</span>
                                        </div>
                                        <div style="color: #2563eb; font-size: 0.9rem;">${p.link}</div>
                                    </div>
                                    <div style="white-space: pre-line; color: #4b5563; font-size: 0.95rem; margin-top: 5px;">${p.desc}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    ${experience.length > 0 ? `
                        <h2 style="${h2Style}">EXPERIENCE</h2>
                        <div style="margin-bottom: 20px;">
                            ${experience.map(e => `
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                                        <div style="font-weight: 700; font-size: 1.05rem; color: #1f2937;">${e.role}</div>
                                        <div style="font-weight: 600; color: #4b5563; font-size: 0.9rem;">${e.duration}</div>
                                    </div>
                                    <div style="font-weight: 600; color: #2563eb; margin-bottom: 3px;">${e.company}</div>
                                    <div style="white-space: pre-line; color: #4b5563; font-size: 0.95rem;">${e.desc}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <h2 style="${h2Style}">TECHNICAL SKILLS</h2>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
                        ${(data.techSkills || data.skills || []).map(s => `
                            <span style="background: #f3f4f6; padding: 4px 12px; border-radius: 4px; color: #1f2937; font-size: 0.9rem; font-weight: 500;">${s}</span>
                        `).join('')}
                    </div>

                    ${(data.softSkills || []).length > 0 ? `
                        <h2 style="${h2Style}">SOFT SKILLS</h2>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px;">
                            ${(data.softSkills || []).map(s => `
                                <span style="background: #f0fdf4; padding: 4px 12px; border-radius: 4px; color: #166534; font-size: 0.9rem; font-weight: 500;">${s}</span>
                            `).join('')}
                        </div>
                    ` : ''}

                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                        ${(data.languages || []).length > 0 ? `
                            <div>
                                <h2 style="${h2Style}">LANGUAGES</h2>
                                <p style="color: #4b5563;">${(data.languages || []).join(', ')}</p>
                            </div>
                        ` : ''}
                        ${(data.achievements || []).length > 0 ? `
                            <div>
                                <h2 style="${h2Style}">ACHIEVEMENTS</h2>
                                <ul style="padding-left: 20px; color: #4b5563; margin: 0;">
                                    ${(data.achievements || []).map(a => `<li style="margin-bottom: 5px;">${a}</li>`).join('')}
                                </ul>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        if (layout === 'fresher2') {
            return `
                <div class="res-body" style="font-family: 'Helvetica Neue', Arial, sans-serif; display: flex; padding: 0; background: #fff; min-height: 1056px;">
                    <!-- LEFT SIDEBAR -->
                    <div style="width: 32%; background: #2d3748; color: #e2e8f0; padding: 40px 25px; box-sizing: border-box;">
                        ${personal.profilePhoto ? `<div style="text-align: center; margin-bottom: 30px;"><img src="${personal.profilePhoto}" style="width: 140px; height: 140px; border-radius: 50%; object-fit: cover; border: 4px solid #4a5568;"></div>` : ''}
                        
                        <div style="margin-bottom: 35px;">
                            <h3 style="color: #fff; font-size: 1.1rem; border-bottom: 1px solid #4a5568; padding-bottom: 8px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Contact</h3>
                            ${personal.phone ? `<div style="margin-bottom: 12px; font-size: 0.9rem;"><span style="font-weight: 600; color: #a0aec0; display: block; font-size: 0.75rem; text-transform: uppercase;">Phone</span>${personal.phone}</div>` : ''}
                            ${personal.email ? `<div style="margin-bottom: 12px; font-size: 0.9rem;"><span style="font-weight: 600; color: #a0aec0; display: block; font-size: 0.75rem; text-transform: uppercase;">Email</span>${personal.email}</div>` : ''}
                            ${personal.location ? `<div style="margin-bottom: 12px; font-size: 0.9rem;"><span style="font-weight: 600; color: #a0aec0; display: block; font-size: 0.75rem; text-transform: uppercase;">Address</span>${personal.location}</div>` : ''}
                            ${personal.linkedin ? `<div style="margin-bottom: 12px; font-size: 0.9rem;"><span style="font-weight: 600; color: #a0aec0; display: block; font-size: 0.75rem; text-transform: uppercase;">LinkedIn</span>${personal.linkedin}</div>` : ''}
                            ${personal.twitter ? `<div style="margin-bottom: 12px; font-size: 0.9rem;"><span style="font-weight: 600; color: #a0aec0; display: block; font-size: 0.75rem; text-transform: uppercase;">Portfolio</span>${personal.twitter}</div>` : ''}
                        </div>

                        ${(data.techSkills || data.skills || []).length > 0 ? `
                        <div style="margin-bottom: 35px;">
                            <h3 style="color: #fff; font-size: 1.1rem; border-bottom: 1px solid #4a5568; padding-bottom: 8px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Expertise</h3>
                            <ul style="list-style-type: none; padding: 0; margin: 0;">
                                ${(data.techSkills || data.skills || []).map(s => `<li style="margin-bottom: 8px; font-size: 0.9rem;">&mdash; ${s}</li>`).join('')}
                            </ul>
                        </div>
                        ` : ''}

                        ${(data.languages || []).length > 0 ? `
                        <div style="margin-bottom: 35px;">
                            <h3 style="color: #fff; font-size: 1.1rem; border-bottom: 1px solid #4a5568; padding-bottom: 8px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;">Languages</h3>
                            <div style="font-size: 0.9rem; color: #e2e8f0;">${(data.languages || []).join(', ')}</div>
                        </div>
                        ` : ''}
                    </div>

                    <!-- MAIN CONTENT -->
                    <div style="width: 68%; padding: 50px 40px; box-sizing: border-box; color: #2d3748;">
                        <h1 style="font-size: 3rem; margin: 0 0 5px 0; color: #1a202c; letter-spacing: -1px; line-height: 1.1;">${personal.fullName || ''}</h1>
                        <div style="font-size: 1.3rem; color: #718096; text-transform: uppercase; font-weight: 600; letter-spacing: 2px; margin-bottom: 25px;">${personal.professionalTitle || ''}</div>
                        
                        <div style="font-size: 0.95rem; line-height: 1.6; color: #4a5568; margin-bottom: 35px;">${personal.summary || ''}</div>

                        ${education.length > 0 ? `
                        <div style="margin-bottom: 30px;">
                            <h2 style="font-size: 1.4rem; color: #1a202c; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 15px;">Education</h2>
                            ${education.map(ed => `
                                <div style="margin-bottom: 15px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <div style="font-weight: 700; color: #2d3748;">${ed.degree}</div>
                                        <div style="font-size: 0.85rem; font-weight: 600; color: #a0aec0;">${ed.year}</div>
                                    </div>
                                    <div style="color: #4a5568; font-style: italic; margin-bottom: 5px;">${ed.school}</div>
                                    <div style="font-size: 0.9rem; color: #718096; white-space: pre-line;">${ed.desc || ''}</div>
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}

                        ${projects.length > 0 ? `
                        <div style="margin-bottom: 30px;">
                            <h2 style="font-size: 1.4rem; color: #1a202c; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 15px;">Selected Projects</h2>
                            ${projects.map(p => `
                                <div style="margin-bottom: 18px;">
                                    <div style="font-weight: 700; color: #2d3748;">${p.name}</div>
                                    <div style="font-size: 0.85rem; color: #718096; margin-bottom: 5px;">${p.technologies} ${p.link ? `&middot; ${p.link}` : ''}</div>
                                    <div style="font-size: 0.9rem; color: #4a5568; white-space: pre-line;">${p.desc}</div>
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}

                        ${experience.length > 0 ? `
                        <div style="margin-bottom: 30px;">
                            <h2 style="font-size: 1.4rem; color: #1a202c; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 15px;">Experience</h2>
                            ${experience.map(e => `
                                <div style="margin-bottom: 20px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <div style="font-weight: 700; color: #2d3748;">${e.role}</div>
                                        <div style="font-size: 0.85rem; font-weight: 600; color: #a0aec0;">${e.duration}</div>
                                    </div>
                                    <div style="color: #4a5568; font-style: italic; margin-bottom: 8px;">${e.company}</div>
                                    <div style="font-size: 0.9rem; color: #4a5568; white-space: pre-line;">${e.desc}</div>
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}
                        
                        ${(data.activities || []).length > 0 ? `
                        <div style="margin-bottom: 30px;">
                            <h2 style="font-size: 1.4rem; color: #1a202c; text-transform: uppercase; border-bottom: 2px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 15px;">Activities</h2>
                            <div style="font-size: 0.9rem; color: #4a5568; white-space: pre-line;">${(data.activities || []).join('\n')}</div>
                        </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        if (layout === 'susanne') {
            const h3Style = "font-family: 'Times New Roman', serif; font-size: 1.15rem; color: #111; margin-bottom: 15px; text-transform: uppercase; font-weight: bold; padding: 0;";
            return `
                <div class="res-body" style="font-family: 'Inter', Arial, sans-serif; color: #333; font-size: 10pt; line-height: 1.5; padding: 40px; background: #fff;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h1 style="font-size: 2.8rem; font-family: 'Times New Roman', serif; color: #222; margin: 0; letter-spacing: 2px; text-transform: uppercase;">${personal.fullName || ''}</h1>
                        <p style="font-size: 0.95rem; color: #555; margin-top: 5px; margin-bottom: 0;">
                            ${personal.location || ''} &#183; ${personal.phone || ''}<br>
                            <span style="color: #166534; font-weight: 600;">${personal.email || ''} &#183; ${personal.linkedin || ''} ${personal.github ? `&#183; ${personal.github}` : ''}</span>
                        </p>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #ddd; margin-bottom: 25px;">
                    <p style="margin-bottom: 35px; color: #444; white-space: pre-line;">${personal.summary || ''}</p>

                    <h3 style="${h3Style}">EXPERIENCE</h3>
                    <div style="margin-bottom: 30px;">
                        ${experience.map(e => `
                            <div style="display: flex; margin-bottom: 20px;">
                                <div style="width: 20px; border-left: 2px dotted #aaa; margin-left: 10px; position: relative;"></div>
                                <div style="flex: 1; padding-left: 15px;">
                                    <div style="font-size: 0.85rem; color: #666; font-weight: 600; text-transform: uppercase; margin-bottom: 2px;">${e.duration}</div>
                                    <div style="font-weight: 700; color: #666; margin-bottom: 6px; text-transform: uppercase;"><span style="color: #166534;">${e.role}</span>, ${e.company}</div>
                                    <div style="white-space: pre-line; margin: 0; color: #444; font-size: 0.95rem;">${e.desc}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <h3 style="${h3Style}">EDUCATION</h3>
                    <div style="margin-bottom: 30px;">
                        ${education.map(ed => `
                            <div style="display: flex; margin-bottom: 20px;">
                                <div style="width: 20px; border-left: 2px dotted #aaa; margin-left: 10px; position: relative;"></div>
                                <div style="flex: 1; padding-left: 15px;">
                                    <div style="font-size: 0.85rem; color: #666; font-weight: 600; text-transform: uppercase; margin-bottom: 2px;">${ed.year}</div>
                                    <div style="font-weight: 700; color: #666; margin-bottom: 6px; text-transform: uppercase;"><span style="color: #166534;">${ed.degree}</span>, ${ed.school}</div>
                                    <div style="white-space: pre-line; margin: 0; color: #444; font-size: 0.95rem;">${ed.desc || ''}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <h3 style="${h3Style}">SKILLS</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 30px; margin-bottom: 30px;">
                        ${(data.techSkills || data.skills || []).map(s => `
                            <div style="display: flex; align-items: flex-start;">
                                <span style="color: #166534; margin-right: 8px; font-size: 1.1rem; line-height: 1;">&bull;</span>
                                <span style="color: #444; font-size: 0.95rem;">${s}</span>
                            </div>
                        `).join('')}
                    </div>

                    ${(data.softSkills || []).length > 0 ? `
                        <h3 style="${h3Style}">SOFT SKILLS</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px;">
                            ${(data.softSkills || []).map(s => `<span style="color: #444; font-size: 0.95rem;">&bull; ${s}</span>`).join('')}
                        </div>
                    ` : ''}

                    ${(data.achievements || []).length > 0 ? `
                        <h3 style="${h3Style}">ACHIEVEMENTS</h3>
                        <ul style="color: #444; margin-bottom: 30px; padding-left: 20px;">
                            ${(data.achievements || []).map(a => `<li style="margin-bottom: 5px;">${a}</li>`).join('')}
                        </ul>
                    ` : ''}

                    <h3 style="${h3Style}">ACTIVITIES</h3>
                    <div style="color: #444; font-size: 0.95rem; white-space: pre-line; margin-bottom: 20px;">${(data.activities || []).join('\n')}</div>
                </div>
            `;
        }

        if (layout === 'marjorie') {
            const h2Style = "font-family: 'Times New Roman', serif; font-size: 1.15rem; text-transform: uppercase; font-weight: bold; border-bottom: 2px solid #000; padding-bottom: 3px; margin: 25px 0 15px;";
            return `
                <div class="res-body" style="font-family: 'Times New Roman', serif; padding: 40px; color: #000; font-size: 11pt; line-height: 1.4; background: #fff;">
                    <div style="display: flex; margin-bottom: 25px; align-items: flex-start; gap: 30px;">
                        <div style="width: 120px; flex-shrink: 0;">
                            ${personal.profilePhoto ? `<img src="${personal.profilePhoto}" style="width: 120px; object-fit: cover;">` : ``}
                        </div>
                        <div style="flex: 1; text-align: center; padding-top: 10px;">
                            <h1 style="font-size: 2.4rem; font-weight: normal; margin: 0 0 15px 0;">${personal.fullName}</h1>
                            <div style="line-height: 1.3;">
                                ${personal.dob ? `<div>Date of birth: ${personal.dob}</div>` : ''}
                                ${personal.phone ? `<div>Phone: ${personal.phone}</div>` : ''}
                                ${personal.email ? `<div>Email: ${personal.email}</div>` : ''}
                                ${personal.location ? `<div>Address: ${personal.location}</div>` : ''}
                            </div>
                        </div>
                    </div>

                    <h2 style="${h2Style}">OBJECTIVE</h2>
                    <div style="margin-bottom: 20px; white-space: pre-wrap;">${personal.summary || ''}</div>

                    <h2 style="${h2Style}">EDUCATION</h2>
                    ${education.map(ed => `
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; font-weight: bold; text-transform: uppercase;">
                                <span>${ed.school}</span>
                                <span>${ed.year}</span>
                            </div>
                            <div style="font-style: italic; white-space: pre-line;">Major: ${ed.degree}</div>
                            ${ed.desc ? `<div style="white-space: pre-line; margin-top: 3px;">${ed.desc}</div>` : ''}
                        </div>
                    `).join('')}

                    <h2 style="${h2Style}">WORK EXPERIENCE</h2>
                    ${experience.map(e => `
                        <div style="margin-bottom: 15px;">
                            <div style="display: flex; justify-content: space-between; font-weight: bold; text-transform: uppercase;">
                                <span>${e.company}</span>
                                <span>${e.duration}</span>
                            </div>
                            <div style="font-style: italic; margin-bottom: 5px;">${e.role}</div>
                            <div style="white-space: pre-line;">${e.desc}</div>
                        </div>
                    `).join('')}

                    <h2 style="${h2Style}">ACTIVITIES</h2>
                    <div style="white-space: pre-line;">${(data.activities || []).join('\n')}</div>

                    <h2 style="${h2Style}">REFERENCES</h2>
                    <div style="white-space: pre-line;">${(data.references || []).join('\n')}</div>
                </div>
            `;
        }

        if (layout === 'john') {
            const h2Container = `display: flex; align-items: center; margin: 25px 0 15px;`;
            const h2Text = `font-family: 'Playfair Display', 'Brush Script MT', cursive; font-size: 2.2rem; font-weight: bold; margin: 0; padding-right: 15px; color: #2d3436;`;
            const h2Line = `flex: 1; border-bottom: 2px solid #ddd; position: relative; top: 10px;`;
            
            return `
                <div class="res-body" style="font-family: 'Inter', sans-serif; padding: 40px; color: #333; line-height: 1.6; background: #fff; font-size: 10pt;">
                    <h1 style="font-family: 'Playfair Display', 'Brush Script MT', cursive; font-size: 3.5rem; margin: 0; color: #2d3436; line-height: 1.2;">${personal.fullName}</h1>
                    <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 25px; color: #444;">${personal.professionalTitle}</div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.95rem; margin-bottom: 25px; font-weight: 600;">
                        <div>
                            <div style="margin-bottom: 10px;"><span style="color: #000;">Phone</span> <span style="color: #666; font-weight: 400; margin-left: 10px;">${personal.phone}</span></div>
                            <div><span style="color: #000;">E-mail</span> <span style="color: #666; font-weight: 400; margin-left: 10px;">${personal.email}</span></div>
                        </div>
                        <div>
                            <div style="margin-bottom: 10px;"><span style="color: #000;">LinkedIn</span> <span style="color: #666; font-weight: 400; margin-left: 10px;">${personal.linkedin}</span></div>
                            <div><span style="color: #000;">Twitter</span> <span style="color: #666; font-weight: 400; margin-left: 10px;">${personal.twitter}</span></div>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 30px; color: #555; white-space: pre-wrap;">${personal.summary}</div>
                    
                    <div style="${h2Container}">
                        <h2 style="${h2Text}">Experience</h2>
                        <div style="${h2Line}"></div>
                    </div>
                    ${experience.map(e => `
                        <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="font-weight: 700; color: #444;">${e.duration}</div>
                            <div>
                                <div style="font-size: 1.1rem; font-weight: 800; color: #333;">${e.role}</div>
                                <div style="font-style: italic; color: #666; margin-bottom: 5px;">${e.company}</div>
                                <div style="white-space: pre-line; color: #555;">${e.desc}</div>
                            </div>
                        </div>
                    `).join('')}
                    
                    <div style="${h2Container}">
                        <h2 style="${h2Text}">Education</h2>
                        <div style="${h2Line}"></div>
                    </div>
                    ${education.map(ed => `
                        <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 20px;">
                            <div style="font-weight: 700; color: #444;">${ed.year}</div>
                            <div>
                                <div style="font-size: 1.1rem; font-weight: 800; color: #333;">${ed.degree}${ed.school ? `, ${ed.school}` : ''}</div>
                                <div style="white-space: pre-line; color: #555; margin-top: 5px;">${ed.desc || ''}</div>
                            </div>
                        </div>
                    `).join('')}

                    <div style="${h2Container}">
                        <h2 style="${h2Text}">Skills</h2>
                        <div style="${h2Line}"></div>
                    </div>
                    ${(data.techSkills || data.skills || []).map(s => `
                        <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 15px;">
                            <div></div>
                            <div>
                                ${s.includes('-') ? `<span style="font-weight: 800; color: #333;">${s.split('-')[0]}</span> - ${s.split('-').slice(1).join('-')}` : `<span style="font-weight: 800;">${s}</span>`}
                            </div>
                        </div>
                    `).join('')}

                    ${(data.softSkills || []).length > 0 ? `
                        <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 15px;">
                            <div style="font-weight: 700; color: #444;">Soft Skills</div>
                            <div style="color: #555;">${(data.softSkills || []).join(', ')}</div>
                        </div>
                    ` : ''}

                    ${(data.achievements || []).length > 0 ? `
                        <div style="${h2Container}">
                            <h2 style="${h2Text}">Achievements</h2>
                            <div style="${h2Line}"></div>
                        </div>
                        ${(data.achievements || []).map(a => `
                            <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 10px;">
                                <div></div>
                                <div style="color: #444;">${a}</div>
                            </div>
                        `).join('')}
                    ` : ''}

                    <div style="${h2Container}">
                        <h2 style="${h2Text}">Software</h2>
                        <div style="${h2Line}"></div>
                    </div>
                    ${(data.software || []).map(sw => {
                        const level = parseInt(sw.level) || 5;
                        const dots = '&#9679;'.repeat(level) + '&#9675;'.repeat(5 - level);
                        return `
                        <div style="display: grid; grid-template-columns: 160px 1fr 120px; gap: 20px; margin-bottom: 15px; align-items: center;">
                            <div></div>
                            <div style="color: #444;">${sw.name}</div>
                            <div style="text-align: right; line-height: 1;">
                                <div style="letter-spacing: 2px; font-size: 1.1rem; color: #2d3436;">${dots}</div>
                                <div style="font-size: 0.85rem; color: #555; margin-top: 2px;">${sw.label || ''}</div>
                            </div>
                        </div>
                        `
                    }).join('')}

                    <div style="${h2Container}">
                        <h2 style="${h2Text}">Certifications</h2>
                        <div style="${h2Line}"></div>
                    </div>
                    ${(data.certifications || []).map(c => `
                        <div style="display: grid; grid-template-columns: 160px 1fr; gap: 20px; margin-bottom: 10px;">
                            <div style="font-weight: 700; color: #444;">${c.split('|')[0] || ''}</div>
                            <div style="color: #444;">${c.split('|').slice(1).join('|') || c}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `<div class="res-body"><h1>Welcome</h1><p>Select a template to begin</p></div>`;
    };

    const updatePreview = () => {
        const html = renderTemplate(resumeData);
        previewContainer.innerHTML = html;
        finalResumeContainer.innerHTML = html;
    };

    templateCards.forEach(card => {
        card.addEventListener('click', () => {
            activeTemplate = card.dataset.template;
            resumeData = JSON.parse(JSON.stringify(demos[activeTemplate]));
            updateFormFields(activeTemplate);
            showScreen('input');
            updatePreview();
        });
    });

    const showScreen = (name) => {
        Object.values(screens).forEach(s => s.classList.remove('active'));
        if (screens[name]) screens[name].classList.add('active');

        document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
        if (name === 'template') document.getElementById('step1-indicator').classList.add('active');
        if (name === 'input') document.getElementById('step2-indicator').classList.add('active');
        if (name === 'final') document.getElementById('step3-indicator').classList.add('active');

        window.scrollTo(0, 0);
    };

    const initGrid = () => {
        Object.keys(demos).forEach(id => {
            const el = document.getElementById(`preview-${id}`);
            if (el) el.innerHTML = renderTemplate(demos[id]);
        });
    };

    document.getElementById('go-to-preview')?.addEventListener('click', () => showScreen('final'));
    document.getElementById('back-to-templates')?.addEventListener('click', () => showScreen('template'));
    document.getElementById('back-to-editor')?.addEventListener('click', () => showScreen('input'));

    document.getElementById('download-pdf')?.addEventListener('click', () => {
        html2pdf().from(finalResumeContainer).save(`${resumeData.personal.fullName}.pdf`);
    });

    if (activeTemplate) {
        updateFormFields(activeTemplate);
        updatePreview();
    }
    
    initGrid();
});
