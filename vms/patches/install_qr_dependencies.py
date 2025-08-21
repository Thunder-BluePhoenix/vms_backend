# vms/patches/v1_0/install_qr_dependencies.py

import frappe
import subprocess
import sys
import os

def execute():
    """Install QR code and other dependencies during migration"""
    
    frappe.flags.in_patch = True
    
    try:
        print("\n" + "="*60)
        print("🚀 VMS DEPENDENCY INSTALLATION PATCH")
        print("="*60)
        
        # Check current installation status
        missing_deps = check_missing_dependencies()
        
        if not missing_deps:
            print("✅ All dependencies already installed!")
            return
        
        print(f"📋 Missing dependencies: {', '.join(missing_deps)}")
        
        # Install missing dependencies
        install_dependencies(missing_deps)
        
        # Verify installation
        verify_installation()
        
        # Setup QR system
        setup_qr_system()
        
        print("\n✅ VMS dependency installation completed successfully!")
        print("🔄 Please restart bench: bench restart")
        print("="*60 + "\n")
        
    except Exception as e:
        error_msg = f"Dependency installation failed: {str(e)}"
        print(f"\n❌ {error_msg}")
        frappe.log_error(error_msg, "VMS Dependency Installation Patch")
        
        print("\n📋 Manual installation commands:")
        print("bench pip install qrcode[pil]")
        print("bench pip install pyzbar") 
        print("bench pip install pandas")
        print("bench pip install openpyxl")
        print("bench restart")
        
    finally:
        frappe.flags.in_patch = False

def check_missing_dependencies():
    """Check which dependencies are missing"""
    dependencies = {
        'qrcode': 'qrcode[pil]',
        'pyzbar': 'pyzbar',
        'pandas': 'pandas', 
        'openpyxl': 'openpyxl',
        'PIL': 'Pillow'
    }
    
    missing = []
    
    for module, package in dependencies.items():
        try:
            if module == 'PIL':
                from PIL import Image
            else:
                __import__(module)
            print(f"✅ {module} - Available")
        except ImportError:
            print(f"❌ {module} - Missing")
            missing.append(package)
    
    return missing

def install_dependencies(missing_deps):
    """Install missing dependencies"""
    print("\n📦 Installing dependencies...")
    
    success_count = 0
    failed_deps = []
    
    for dep in missing_deps:
        try:
            print(f"\n🔄 Installing {dep}...")
            
            # Use pip to install the dependency
            result = subprocess.run([
                sys.executable, '-m', 'bench', 'pip', 'install', dep, '--upgrade'
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Successfully installed {dep}")
                success_count += 1
            else:
                print(f"❌ Failed to install {dep}")
                print(f"Error: {result.stderr}")
                failed_deps.append(dep)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout installing {dep}")
            failed_deps.append(dep)
        except Exception as e:
            print(f"❌ Error installing {dep}: {str(e)}")
            failed_deps.append(dep)
    
    print(f"\n📊 Installation Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {len(failed_deps)}")
    
    if failed_deps:
        print(f"   📋 Failed packages: {', '.join(failed_deps)}")
        
        # Log failed installations
        frappe.log_error(
            f"Failed to install dependencies: {failed_deps}", 
            "VMS Dependency Installation"
        )

def verify_installation():
    """Verify that dependencies were installed correctly"""
    print("\n🔍 Verifying installation...")
    
    verification_results = {}
    
    # Test qrcode
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data('Test')
        qr.make(fit=True)
        verification_results['qrcode'] = True
        print("✅ QR Code generation - Working")
    except Exception as e:
        verification_results['qrcode'] = False
        print(f"❌ QR Code generation - Failed: {str(e)}")
    
    # Test PIL
    try:
        from PIL import Image
        import io
        
        # Test image creation
        img = Image.new('RGB', (100, 100), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        verification_results['PIL'] = True
        print("✅ PIL/Pillow - Working")
    except Exception as e:
        verification_results['PIL'] = False
        print(f"❌ PIL/Pillow - Failed: {str(e)}")
    
    # Test pyzbar (optional)
    try:
        import pyzbar
        verification_results['pyzbar'] = True
        print("✅ PyZBar (QR scanning) - Available")
    except ImportError:
        verification_results['pyzbar'] = False
        print("⚠️  PyZBar (QR scanning) - Not available (optional)")
    
    # Test pandas
    try:
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        verification_results['pandas'] = True
        print("✅ Pandas - Working")
    except Exception as e:
        verification_results['pandas'] = False
        print(f"❌ Pandas - Failed: {str(e)}")
    
    # Test openpyxl
    try:
        import openpyxl
        verification_results['openpyxl'] = True
        print("✅ OpenPyXL - Available")
    except ImportError:
        verification_results['openpyxl'] = False
        print("❌ OpenPyXL - Not available")
    
    # Check critical dependencies
    critical_deps = ['qrcode', 'PIL']
    critical_failed = [dep for dep in critical_deps if not verification_results.get(dep, False)]
    
    if critical_failed:
        error_msg = f"Critical dependencies failed verification: {critical_failed}"
        print(f"\n❌ {error_msg}")
        frappe.log_error(error_msg, "VMS Critical Dependency Verification")
    else:
        print("\n✅ All critical dependencies verified successfully!")
    
    return verification_results

def setup_qr_system():
    """Setup QR code system directories and configurations"""
    print("\n🔧 Setting up QR code system...")
    
    try:
        # Create QR code directories
        site_path = frappe.utils.get_site_path()
        
        qr_directories = [
            os.path.join(site_path, 'public', 'files', 'qr_codes'),
            os.path.join(site_path, 'private', 'files', 'qr_codes')
        ]
        
        for qr_dir in qr_directories:
            os.makedirs(qr_dir, exist_ok=True)
            # Set proper permissions
            os.chmod(qr_dir, 0o755)
            print(f"📁 Created directory: {qr_dir}")
        
        # Test QR generation and file saving
        test_qr_system()
        
        print("✅ QR code system setup completed")
        
    except Exception as e:
        error_msg = f"QR system setup failed: {str(e)}"
        print(f"❌ {error_msg}")
        frappe.log_error(error_msg, "VMS QR System Setup")

def test_qr_system():
    """Test QR code generation and file operations"""
    try:
        import qrcode
        import io
        from frappe.utils.file_manager import save_file
        
        # Generate test QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data('VMS QR System Test')
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Test file saving
        filename = "test_qr_system.png"
        file_doc = save_file(
            filename,
            img_buffer.getvalue(),
            "File",  # Using File doctype for test
            None,
            decode=False,
            is_private=0
        )
        
        # Clean up test file
        if file_doc:
            frappe.delete_doc("File", file_doc.name, ignore_permissions=True)
        
        print("✅ QR system test successful")
        
    except Exception as e:
        print(f"⚠️  QR system test failed: {str(e)}")

# Utility function for manual execution
def manual_install():
    """Manual installation function that can be called from console"""
    execute()

# Version check function
def get_installed_versions():
    """Get versions of installed packages"""
    packages = ['qrcode', 'pyzbar', 'pandas', 'openpyxl', 'Pillow']
    versions = {}
    
    for package in packages:
        try:
            if package == 'Pillow':
                import PIL
                versions[package] = getattr(PIL, '__version__', 'Unknown')
            else:
                module = __import__(package)
                versions[package] = getattr(module, '__version__', 'Unknown')
        except ImportError:
            versions[package] = 'Not installed'
    
    return versions

# Create API endpoint for checking status
@frappe.whitelist()
def check_dependency_status():
    """API endpoint to check dependency installation status"""
    try:
        missing_deps = check_missing_dependencies()
        versions = get_installed_versions()
        
        return {
            "success": True,
            "missing_dependencies": missing_deps,
            "installed_versions": versions,
            "qr_system_ready": len(missing_deps) == 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }