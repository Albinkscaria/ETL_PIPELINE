"""Test runner script."""
import subprocess
import sys

def run_tests():
    """Run all tests with coverage."""
    print("=" * 80)
    print("Running Tests with Coverage")
    print("=" * 80)
    
    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "--cov=.",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-v"
    ])
    
    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        print("\nCoverage report generated in htmlcov/index.html")
    else:
        print("\n" + "=" * 80)
        print("✗ Some tests failed")
        print("=" * 80)
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
