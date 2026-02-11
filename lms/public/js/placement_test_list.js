// Custom JavaScript for Placement Test list view
lms.placement_test_list = {
    setup: function(list_view) {
        // Add a custom button to view submissions
        list_view.page.add_action_item(__('View Submissions'), function() {
            var selected_items = list_view.get_checked_items();
            if (selected_items.length === 1) {
                frappe.set_route('List', 'Placement Test Submission', {
                    'placement_test': selected_items[0].name
                });
            } else {
                frappe.msgprint(__('Please select a single test to view submissions.'));
            }
        });

        // Add a button to preview the test
        list_view.page.add_action_item(__('Preview Test'), function() {
            var selected_items = list_view.get_checked_items();
            if (selected_items.length === 1) {
                var test_id = selected_items[0].name;
                window.open('/placement-test?test_id=' + test_id, '_blank');
            } else {
                frappe.msgprint(__('Please select a single test to preview.'));
            }
        });
    }
};
