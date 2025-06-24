#!/usr/bin/env python3
"""
Basic test script to verify the application structure and imports
without requiring external dependencies.
"""

import sys
import os
import importlib.util

def test_file_structure():
    """Test that all required files exist."""
    print("🔍 Testing File Structure")
    print("=" * 40)
    
    required_files = [
        'src/main.py',
        'src/config/settings.py',
        'src/services/cloudwatch_service.py',
        'src/utils/aws_client.py',
        'src/utils/data_processor.py',
        'src/components/ui_components.py',
        'src/components/charts.py',
        'tests/test_data_processor.py',
        'tests/test_aws_client.py',
        'tests/test_cloudwatch_service.py',
        'requirements/requirements.txt',
        'README.md',
        'Dockerfile',
        'Makefile'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present")
        return True

def test_python_syntax():
    """Test Python syntax of all source files."""
    print("\n🐍 Testing Python Syntax")
    print("=" * 40)
    
    python_files = []
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"   ✅ {file_path}")
        except SyntaxError as e:
            print(f"   ❌ {file_path}: {e}")
            syntax_errors.append(file_path)
        except Exception as e:
            print(f"   ⚠️  {file_path}: {e}")
    
    if syntax_errors:
        print(f"\n❌ Syntax errors in {len(syntax_errors)} files")
        return False
    else:
        print(f"\n✅ All {len(python_files)} Python files have valid syntax")
        return True

def test_imports():
    """Test basic imports without external dependencies."""
    print("\n📦 Testing Basic Imports")
    print("=" * 40)
    
    # Test configuration imports
    try:
        sys.path.insert(0, os.path.abspath('.'))
        
        # Test settings import
        spec = importlib.util.spec_from_file_location("settings", "src/config/settings.py")
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        print("   ✅ Configuration settings")
        
        # Test that configuration classes exist
        assert hasattr(settings, 'AWSConfig')
        assert hasattr(settings, 'AppConfig')
        assert hasattr(settings, 'LogAnalysisConfig')
        print("   ✅ Configuration classes")
        
        # Test configuration functions
        assert hasattr(settings, 'get_aws_regions')
        assert hasattr(settings, 'get_time_range_options')
        print("   ✅ Configuration functions")
        
        # Test configuration instances
        aws_config = settings.aws_config
        app_config = settings.app_config
        log_config = settings.log_config
        print("   ✅ Configuration instances")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False

def test_project_structure():
    """Test project structure follows best practices."""
    print("\n🏗️  Testing Project Structure")
    print("=" * 40)
    
    # Check for proper package structure
    required_dirs = [
        'src',
        'src/config',
        'src/services',
        'src/utils',
        'src/components',
        'tests',
        'docs',
        'requirements'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if os.path.isdir(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/")
            missing_dirs.append(dir_path)
    
    # Check for __init__.py files
    init_files = [
        'src/__init__.py',
        'src/config/__init__.py',
        'src/services/__init__.py',
        'src/utils/__init__.py',
        'src/components/__init__.py',
        'tests/__init__.py'
    ]
    
    for init_file in init_files:
        if os.path.exists(init_file):
            print(f"   ✅ {init_file}")
        else:
            print(f"   ❌ {init_file}")
            missing_dirs.append(init_file)
    
    if missing_dirs:
        print(f"\n❌ Missing {len(missing_dirs)} directories/files")
        return False
    else:
        print(f"\n✅ Project structure is correct")
        return True

def test_documentation():
    """Test documentation completeness."""
    print("\n📚 Testing Documentation")
    print("=" * 40)
    
    doc_files = [
        'README.md',
        'docs/ARCHITECTURE.md',
        'docs/API.md'
    ]
    
    missing_docs = []
    for doc_file in doc_files:
        if os.path.exists(doc_file) and os.path.getsize(doc_file) > 100:
            print(f"   ✅ {doc_file}")
        else:
            print(f"   ❌ {doc_file}")
            missing_docs.append(doc_file)
    
    if missing_docs:
        print(f"\n❌ Missing or empty documentation files: {len(missing_docs)}")
        return False
    else:
        print(f"\n✅ All documentation files present and non-empty")
        return True

def main():
    """Run all basic tests."""
    print("🧪 AWS CloudWatch Log Analyzer - Basic Tests")
    print("=" * 60)
    print("Running basic tests without external dependencies...")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_python_syntax,
        test_project_structure,
        test_documentation,
        test_imports
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All basic tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements/requirements.txt")
        print("2. Configure AWS credentials")
        print("3. Run: streamlit run src/main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    
    print("=" * 60)
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
