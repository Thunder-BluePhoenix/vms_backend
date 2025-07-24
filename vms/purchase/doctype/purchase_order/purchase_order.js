// Universal Scrollable Version History for both RFQ and Quotation
frappe.ui.form.on('Purchase Order', {
    refresh: function(frm) {
        generate_universal_scrollable_version_history(frm);
    },
    version_history_on_form_rendered: function(frm) {
        setTimeout(() => generate_universal_scrollable_version_history(frm), 100);
    }
});

// frappe.ui.form.on('Quotation', {
//     refresh: function(frm) {
//         generate_universal_scrollable_version_history(frm);
//     },
//     version_history_on_form_rendered: function(frm) {
//         setTimeout(() => generate_universal_scrollable_version_history(frm), 100);
//     }
// });

function generate_universal_scrollable_version_history(frm) {
    if (!frm.doc.version_history || frm.doc.version_history.length === 0) {
        frm.fields_dict['history_html'].html(`
            <div style="text-align: center; padding: 40px; color: #6c757d; background: #f8f9fa; border-radius: 8px; border: 1px solid #e9ecef;">
                <i class="fa fa-history fa-2x" style="margin-bottom: 12px; opacity: 0.4;"></i>
                <h5 style="margin: 0; font-weight: 500;">No Version History</h5>
                <p style="margin: 8px 0 0 0; font-size: 13px;">Changes to this document will appear here</p>
            </div>
        `);
        return;
    }

    const sortedHistory = frm.doc.version_history.slice().sort((a, b) => 
        new Date(b.date_and_time) - new Date(a.date_and_time)
    );

    const doctype = frm.doc.doctype;
    const isQuotation = doctype === 'Quotation';
    
    // Color schemes for different doctypes with better contrast
    const colorConfig = {
        'Quotation': {
            headerGradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
            cardHeaderColor: '#047857',
            accentColor: '#065f46'
        },
        'Request For Quotation': {
            headerGradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            cardHeaderColor: '#6b21a8',
            accentColor: '#581c87'
        }
    };

    const config = colorConfig[doctype] || colorConfig['Request For Quotation'];
    const doctypeIcon = isQuotation ? '💰' : '📋';

    let html = `
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            <style>
                .uni-scroll-version-container {
                    background: #fff;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    overflow: hidden;
                }
                .uni-scroll-version-header-main {
                    background: ${config.headerGradient};
                    color: white;
                    padding: 12px 16px;
                    text-align: center;
                    border-bottom: 1px solid rgba(255,255,255,0.2);
                    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                }
                .uni-scroll-version-header-title {
                    font-size: 14px;
                    font-weight: 600;
                    margin: 0;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.3);
                }
                .uni-scroll-container {
                    overflow-x: auto;
                    overflow-y: hidden;
                    padding: 16px;
                    background: #f8f9fa;
                }
                .uni-scroll-container::-webkit-scrollbar {
                    height: 8px;
                }
                .uni-scroll-container::-webkit-scrollbar-track {
                    background: #f1f3f4;
                    border-radius: 4px;
                }
                .uni-scroll-container::-webkit-scrollbar-thumb {
                    background: ${config.cardHeaderColor};
                    border-radius: 4px;
                }
                .uni-scroll-container::-webkit-scrollbar-thumb:hover {
                    background: ${config.accentColor};
                }
                .uni-version-scroll-grid {
                    display: flex;
                    gap: 16px;
                    min-width: max-content;
                    padding-bottom: 4px;
                }
                .uni-scroll-prof-version { 
                    background: #fff;
                    border: 1px solid #e0e6ed;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                    transition: all 0.3s ease;
                    min-width: 280px;
                    max-width: 320px;
                    flex-shrink: 0;
                }
                .uni-scroll-prof-version:hover {
                    border-color: ${config.cardHeaderColor};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    transform: translateY(-2px);
                }
                .uni-scroll-prof-header {
                    background: ${config.cardHeaderColor};
                    color: white;
                    padding: 10px 14px;
                    font-size: 13px;
                    font-weight: 600;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-radius: 8px 8px 0 0;
                    text-shadow: 0 1px 2px rgba(0,0,0,0.2);
                }
                .uni-scroll-prof-version-badge {
                    background: rgba(255,255,255,0.25);
                    padding: 3px 8px;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: 700;
                    text-shadow: none;
                    border: 1px solid rgba(255,255,255,0.3);
                }
                .uni-scroll-prof-content {
                    padding: 14px;
                    max-height: 400px;
                    overflow-y: auto;
                }
                .uni-scroll-prof-content::-webkit-scrollbar {
                    width: 4px;
                }
                .uni-scroll-prof-content::-webkit-scrollbar-track {
                    background: #f8f9fa;
                }
                .uni-scroll-prof-content::-webkit-scrollbar-thumb {
                    background: #dee2e6;
                    border-radius: 2px;
                }
                .uni-scroll-prof-datetime {
                    color: #6c757d; 
                    font-size: 11px; 
                    margin-bottom: 10px; 
                    text-align: center;
                    background: #f8f9fa;
                    padding: 4px 8px;
                    border-radius: 4px;
                    border: 1px solid #e9ecef;
                }
                .uni-scroll-prof-summary {
                    background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
                    color: ${config.accentColor};
                    font-size: 11px;
                    font-weight: 600;
                    padding: 6px 10px;
                    border-radius: 16px;
                    margin-bottom: 10px;
                    text-align: center;
                    border: 1px solid rgba(0,0,0, 0.1);
                    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
                }
                .uni-scroll-prof-change {
                    background: #f8f9fa;
                    border-left: 3px solid ${config.cardHeaderColor};
                    padding: 8px 10px;
                    margin: 6px 0;
                    border-radius: 0 6px 6px 0;
                    transition: all 0.2s ease;
                    border-top: 1px solid #e9ecef;
                    border-right: 1px solid #e9ecef;
                    border-bottom: 1px solid #e9ecef;
                }
                .uni-scroll-prof-change:hover {
                    background: #e9ecef;
                    transform: translateX(2px);
                }
                .uni-scroll-prof-field {
                    font-weight: 600;
                    color: #212529;
                    font-size: 12px;
                    margin-bottom: 6px;
                    text-transform: capitalize;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                .uni-scroll-prof-values {
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                    font-size: 11px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                .uni-scroll-prof-old {
                    color: #dc3545;
                    background: rgba(220, 53, 69, 0.1);
                    padding: 3px 8px;
                    border-radius: 4px;
                    text-decoration: line-through;
                    border: 1px solid rgba(220, 53, 69, 0.3);
                    font-weight: 500;
                }
                .uni-scroll-prof-new {
                    color: #198754;
                    background: rgba(25, 135, 84, 0.1);
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-weight: 600;
                    border: 1px solid rgba(25, 135, 84, 0.3);
                }
                .uni-scroll-prof-arrow {
                    color: #6c757d;
                    font-size: 14px;
                    font-weight: bold;
                }
                .uni-scroll-prof-table {
                    background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
                    border-left-color: #f39c12;
                }
                .uni-scroll-prof-table-name {
                    font-size: 11px;
                    color: #b45309;
                    font-weight: 700;
                    margin-bottom: 6px;
                    background: rgba(255, 193, 7, 0.2);
                    padding: 3px 8px;
                    border-radius: 4px;
                    display: inline-flex;
                    align-items: center;
                    gap: 4px;
                    border: 1px solid rgba(243, 156, 18, 0.3);
                }
                .uni-scroll-prof-empty {
                    color: #adb5bd;
                    font-style: italic;
                    background: #f8f9fa;
                    padding: 3px 8px;
                    border-radius: 4px;
                    border: 1px solid #e9ecef;
                    font-weight: 500;
                }
                .uni-scroll-prof-no-changes {
                    text-align: center;
                    color: #6c757d;
                    font-style: italic;
                    padding: 20px;
                    font-size: 12px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border-radius: 6px;
                    border: 2px dashed #dee2e6;
                }
                .uni-scroll-hint {
                    text-align: center;
                    color: #6c757d;
                    font-size: 11px;
                    padding: 8px 16px;
                    background: #fff;
                    border-top: 1px solid #e9ecef;
                    font-style: italic;
                }
                @media (max-width: 768px) {
                    .uni-scroll-prof-version {
                        min-width: 260px;
                        max-width: 280px;
                    }
                    .uni-scroll-prof-values {
                        flex-direction: column;
                        align-items: flex-start;
                        gap: 4px;
                    }
                    .uni-scroll-prof-arrow {
                        transform: rotate(90deg);
                    }
                }
            </style>
            
            <div class="uni-scroll-version-container">
                <div class="uni-scroll-version-header-main">
                    <h4 class="uni-scroll-version-header-title">${doctypeIcon} ${doctype} Version History (${sortedHistory.length} versions)</h4>
                </div>
                <div class="uni-scroll-container">
                    <div class="uni-version-scroll-grid">
    `;

    // Generate all version cards in horizontal layout
    sortedHistory.forEach((entry, index) => {
        const versionNumber = sortedHistory.length - index;
        html += generateUniversalScrollableVersionCard(entry, versionNumber);
    });

    html += `
                    </div>
                </div>
                <div class="uni-scroll-hint">
                    💡 Scroll horizontally to view all versions • Latest versions appear first
                </div>
            </div>
        </div>
    `;

    frm.fields_dict['history_html'].html(html);
}

function generateUniversalScrollableVersionCard(entry, versionNumber) {
    const versionData = JSON.parse(entry.field_json || '{"changed": [], "row_changed": []}');
    const timeAgo = frappe.datetime.comment_when(entry.date_and_time);
    const formattedDate = frappe.datetime.str_to_user(entry.date_and_time);

    const fieldChangesCount = versionData.changed ? versionData.changed.length : 0;
    const tableChangesCount = versionData.row_changed ? versionData.row_changed.length : 0;

    let cardHtml = `
        <div class="uni-scroll-prof-version">
            <div class="uni-scroll-prof-header">
                <span>Version ${versionNumber}</span>
                <span class="uni-scroll-prof-version-badge">v${versionNumber}</span>
            </div>
            <div class="uni-scroll-prof-content">
                <div class="uni-scroll-prof-datetime">
                    📅 ${formattedDate}<br>⏰ ${timeAgo}
                </div>
    `;

    // Summary
    if (fieldChangesCount > 0 || tableChangesCount > 0) {
        const changes = [];
        if (fieldChangesCount > 0) changes.push(`${fieldChangesCount} field${fieldChangesCount > 1 ? 's' : ''}`);
        if (tableChangesCount > 0) changes.push(`${tableChangesCount} table${tableChangesCount > 1 ? 's' : ''}`);
        cardHtml += `<div class="uni-scroll-prof-summary">📊 ${changes.join(' • ')} changed</div>`;
    }

    // Field Changes
    if (versionData.changed && versionData.changed.length > 0) {
        versionData.changed.forEach(change => {
            const [fieldName, oldValue, newValue] = change;
            const displayName = fieldName.replace(/_/g, ' ');
            
            cardHtml += `
                <div class="uni-scroll-prof-change">
                    <div class="uni-scroll-prof-field">🏷️ ${displayName}</div>
                    <div class="uni-scroll-prof-values">
                        <span class="uni-scroll-prof-old">${oldValue || '<span class="uni-scroll-prof-empty">empty</span>'}</span>
                        <span class="uni-scroll-prof-arrow">→</span>
                        <span class="uni-scroll-prof-new">${newValue || '<span class="uni-scroll-prof-empty">empty</span>'}</span>
                    </div>
                </div>
            `;
        });
    }

    // Table Changes
    if (versionData.row_changed && versionData.row_changed.length > 0) {
        versionData.row_changed.forEach(rowChange => {
            const [tableName, rowIndex, rowId, changes] = rowChange;
            const displayTableName = tableName.replace(/_/g, ' ');

            cardHtml += `<div class="uni-scroll-prof-change uni-scroll-prof-table">
                <div class="uni-scroll-prof-table-name">📋 ${displayTableName} [Row ${parseInt(rowIndex) + 1}]</div>`;

            if (changes && changes.length > 0) {
                changes.forEach(change => {
                    const [fieldName, oldValue, newValue] = change;
                    const displayFieldName = fieldName.replace(/_/g, ' ');

                    cardHtml += `
                        <div class="uni-scroll-prof-field">📝 ${displayFieldName}</div>
                        <div class="uni-scroll-prof-values">
                            <span class="uni-scroll-prof-old">${oldValue || '<span class="uni-scroll-prof-empty">empty</span>'}</span>
                            <span class="uni-scroll-prof-arrow">→</span>
                            <span class="uni-scroll-prof-new">${newValue || '<span class="uni-scroll-prof-empty">empty</span>'}</span>
                        </div>
                    `;
                });
            }

            cardHtml += '</div>';
        });
    }

    // No changes
    if (fieldChangesCount === 0 && tableChangesCount === 0) {
        cardHtml += '<div class="uni-scroll-prof-no-changes">ℹ️ No changes recorded</div>';
    }

    cardHtml += '</div></div>';
    
    return cardHtml;
}