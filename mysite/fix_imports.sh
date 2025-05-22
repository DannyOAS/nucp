#!/bin/bash
# Quick fix for import errors - Run this to fix all import issues

echo "🔧 Fixing import errors in patient views..."

# OPTION 1: Quick compatibility fix - Add old decorator back to decorators.py
echo "Adding compatibility decorator to patient/decorators.py..."

# Create backup
cp patient/decorators.py patient/decorators.py.backup

# Add compatibility function to decorators.py
cat >> patient/decorators.py << 'EOF'

# COMPATIBILITY: Keep old decorator but make it use the secure version
def patient_required(view_func):
    """
    COMPATIBILITY: Old decorator that now uses secure implementation
    This allows existing code to work while gradually migrating to patient_required_secure
    """
    logger.warning(f"DEPRECATED: View {view_func.__name__} is using deprecated @patient_required decorator. Update to @patient_required_secure")
    return patient_required_secure(view_func)
EOF

# Add compatibility function to utils.py
echo "Adding compatibility function to patient/utils.py..."

# Create backup
cp patient/utils.py patient/utils.py.backup

# Add compatibility function to utils.py
cat >> patient/utils.py << 'EOF'

# COMPATIBILITY: Keep old function but make it use secure version
def get_current_patient(request):
    """
    COMPATIBILITY: Old function that now uses secure implementation
    """
    logger.warning("DEPRECATED: get_current_patient() is deprecated. Use get_current_patient_secure()")
    return get_current_patient_secure(request)
EOF

echo "✅ Compatibility functions added"

# OPTION 2: Update all view files (more thorough but requires more changes)
echo "🔍 Checking which view files need updating..."

# Find all files using the old imports
grep -r "patient_required[^_]" patient/views/ > old_imports.txt
grep -r "get_current_patient[^_]" patient/views/ >> old_imports.txt

if [ -s old_imports.txt ]; then
    echo "📝 Files that should be updated to use secure versions:"
    cat old_imports.txt
    echo ""
    echo "⚠️  RECOMMENDATION: Gradually update these files to use:"
    echo "   @patient_required_secure instead of @patient_required"
    echo "   get_current_patient_secure() instead of get_current_patient()"
else
    echo "✅ No files found using old imports"
fi

# Clean up
rm -f old_imports.txt

echo ""
echo "🎉 IMPORT ERROR FIXES COMPLETE!"
echo ""
echo "✅ IMMEDIATE FIX APPLIED:"
echo "  • Added patient_required() compatibility function"
echo "  • Added get_current_patient() compatibility function"
echo "  • All existing code should now work"
echo ""
echo "📋 NEXT STEPS (RECOMMENDED):"
echo "  1. Test that the application starts without import errors"
echo "  2. Gradually update views to use secure versions:"
echo "     - Replace @patient_required with @patient_required_secure"
echo "     - Replace get_current_patient() with get_current_patient_secure()"
echo "  3. Remove compatibility functions once all views are updated"
echo ""
echo "🔍 TO TEST:"
echo "  python manage.py runserver"
echo ""
echo "📊 MIGRATION STATUS:"
echo "  • Security fixes: ✅ Applied"
echo "  • Import compatibility: ✅ Fixed"
echo "  • Full migration to secure functions: 🔄 In Progress"
