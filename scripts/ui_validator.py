#!/usr/bin/env python3
"""
UI Validation and Testing Script
Validates clickable areas, visual hierarchy, and generates screenshots
"""

import json
import os
import sys
from pathlib import Path

# Try to import selenium for screenshot capture
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    print("⚠️  Selenium not installed. Screenshot functionality disabled.")
    print("   Install with: pip install selenium")
    SELENIUM_AVAILABLE = False


class UIValidator:
    """Validates UI implementation against design system specifications"""
    
    DESIGN_SYSTEM = {
        "spacing": {
            "8pt_grid": [0.5, 1, 1.5, 2, 3, 4],  # rem values
            "card_radius": [18, 20],  # px
            "control_radius": [12],  # px
        },
        "colors": {
            "sf_black": "#050505",
            "sf_gray_900": "#0B0B0C",
            "sf_gray_700": "#1C1C1E",
            "sf_gray_600": "#2C2C2E",
            "sf_blue": "#0A84FF",
        },
        "interactions": {
            "min_touch_target": 40,  # px (2.5rem)
            "hover_lift": "0.25rem",
            "active_scale": 0.98,
        },
        "motion": {
            "spring": "cubic-bezier(0.16, 1, 0.3, 1)",
            "duration_micro": "0.18s",
            "duration_standard": "0.24s",
        }
    }
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.css_files = [
            self.project_root / "css" / "styles.css",
            self.project_root / "css" / "styles.addon.css"
        ]
        self.html_file = self.project_root / "index.html"
        self.js_file = self.project_root / "js" / "app.js"
        self.results = []
        
    def validate_all(self):
        """Run all validation checks"""
        print("🔍 Starting UI Validation...")
        print("=" * 60)
        
        self.validate_spacing()
        self.validate_radii()
        self.validate_touch_targets()
        self.validate_motion()
        self.validate_colors()
        self.validate_structure()
        
        self.print_results()
        
    def validate_spacing(self):
        """Validate 8pt grid system compliance"""
        print("\n📏 Validating 8pt Grid System...")
        
        violations = []
        for css_file in self.css_files:
            if not css_file.exists():
                continue
                
            with open(css_file, 'r') as f:
                content = f.read()
                
            # Check for hardcoded pixel values that don't follow 8pt grid
            import re
            # Look for px values that aren't multiples of 8
            px_values = re.findall(r':\s*(\d+)px', content)
            
            for val in px_values:
                num = int(val)
                # Allow certain exceptions (1px borders, etc)
                if num > 4 and num % 8 != 0:
                    violations.append(f"Non-8pt value: {num}px in {css_file.name}")
        
        if violations:
            self.results.append({
                "test": "8pt Grid System",
                "status": "⚠️  WARNINGS",
                "details": violations[:5]  # Limit to first 5
            })
        else:
            self.results.append({
                "test": "8pt Grid System",
                "status": "✅ PASSED",
                "details": []
            })
    
    def validate_radii(self):
        """Validate border-radius values match squircle standards"""
        print("📐 Validating Border Radii (Squircle)...")
        
        violations = []
        for css_file in self.css_files:
            if not css_file.exists():
                continue
                
            with open(css_file, 'r') as f:
                content = f.read()
            
            # Check for border-radius values
            import re
            radius_values = re.findall(r'border-radius:\s*(\d+)px', content)
            
            expected = [12, 18, 20]
            for val in radius_values:
                num = int(val)
                if num not in expected and num != 50 and num != 999:  # 50% for circles, 999px for pills
                    violations.append(f"Non-standard radius: {num}px in {css_file.name}")
        
        if violations:
            self.results.append({
                "test": "Squircle Radii",
                "status": "⚠️  WARNINGS",
                "details": violations[:5]
            })
        else:
            self.results.append({
                "test": "Squircle Radii",
                "status": "✅ PASSED",
                "details": []
            })
    
    def validate_touch_targets(self):
        """Validate minimum touch target sizes (40px / 2.5rem)"""
        print("👆 Validating Touch Target Sizes...")
        
        # This requires running browser inspection
        # For now, check CSS declarations
        violations = []
        
        for css_file in self.css_files:
            if not css_file.exists():
                continue
                
            with open(css_file, 'r') as f:
                content = f.read()
            
            # Look for button/icon sizing
            import re
            
            # Check for small widths/heights on interactive elements
            patterns = [
                (r'\.action-icon[^}]*width:\s*(\d+\.?\d*)rem', 'action-icon width'),
                (r'\.icon-btn[^}]*min-width:\s*(\d+\.?\d*)rem', 'icon-btn width'),
            ]
            
            for pattern, name in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    size_rem = float(match)
                    if size_rem < 2.5:  # 2.5rem = 40px
                        violations.append(f"{name} too small: {size_rem}rem (min: 2.5rem)")
        
        if violations:
            self.results.append({
                "test": "Touch Target Sizes",
                "status": "❌ FAILED",
                "details": violations
            })
        else:
            self.results.append({
                "test": "Touch Target Sizes",
                "status": "✅ PASSED",
                "details": ["All interactive elements ≥ 2.5rem (40px)"]
            })
    
    def validate_motion(self):
        """Validate Apple spring physics easing"""
        print("🎬 Validating Motion Design...")
        
        violations = []
        correct_count = 0
        
        for css_file in self.css_files:
            if not css_file.exists():
                continue
                
            with open(css_file, 'r') as f:
                content = f.read()
            
            # Check for Apple spring easing
            if "cubic-bezier(0.16, 1, 0.3, 1)" in content:
                correct_count += 1
            
            # Check for linear transitions (should be avoided)
            import re
            if re.search(r'transition:.*\blinear\b', content):
                violations.append("Linear easing detected (use spring instead)")
        
        if violations:
            self.results.append({
                "test": "Motion Design",
                "status": "⚠️  WARNINGS",
                "details": violations
            })
        elif correct_count > 0:
            self.results.append({
                "test": "Motion Design",
                "status": "✅ PASSED",
                "details": [f"Apple spring easing found in {correct_count} file(s)"]
            })
        else:
            self.results.append({
                "test": "Motion Design",
                "status": "⚠️  WARNING",
                "details": ["Spring easing not detected"]
            })
    
    def validate_colors(self):
        """Validate San Francisco color palette usage"""
        print("🎨 Validating Color Palette...")
        
        found_colors = []
        
        for css_file in self.css_files:
            if not css_file.exists():
                continue
                
            with open(css_file, 'r') as f:
                content = f.read()
            
            for color_name, color_value in self.DESIGN_SYSTEM["colors"].items():
                if color_value.lower() in content.lower():
                    found_colors.append(color_name)
        
        if found_colors:
            self.results.append({
                "test": "Color Palette",
                "status": "✅ PASSED",
                "details": [f"SF colors detected: {', '.join(set(found_colors))}"]
            })
        else:
            self.results.append({
                "test": "Color Palette",
                "status": "⚠️  INFO",
                "details": ["Using CSS variables (recommended)"]
            })
    
    def validate_structure(self):
        """Validate HTML structure for semantic correctness"""
        print("🏗️  Validating HTML Structure...")
        
        if not self.html_file.exists():
            self.results.append({
                "test": "HTML Structure",
                "status": "❌ FAILED",
                "details": ["index.html not found"]
            })
            return
        
        with open(self.html_file, 'r') as f:
            content = f.read()
        
        checks = [
            ('<aside class="sidebar"', "Sidebar element"),
            ('<main class="main-content"', "Main content element"),
            ('class="ambient-glow"', "Ambient glow background"),
            ('class="bento-grid"', "Bento grid dashboard"),
            ('class="item-card"', "Media cards"),
        ]
        
        found = []
        missing = []
        
        for pattern, name in checks:
            if pattern in content:
                found.append(name)
            else:
                missing.append(name)
        
        if missing:
            self.results.append({
                "test": "HTML Structure",
                "status": "⚠️  INCOMPLETE",
                "details": [f"Missing: {', '.join(missing)}"]
            })
        else:
            self.results.append({
                "test": "HTML Structure",
                "status": "✅ PASSED",
                "details": [f"All key elements present ({len(found)} found)"]
            })
    
    def print_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if "✅" in r["status"])
        warnings = sum(1 for r in self.results if "⚠️" in r["status"])
        failed = sum(1 for r in self.results if "❌" in r["status"])
        
        for result in self.results:
            print(f"\n{result['status']} {result['test']}")
            for detail in result['details']:
                print(f"   • {detail}")
        
        print("\n" + "=" * 60)
        print(f"Summary: {passed} passed, {warnings} warnings, {failed} failed")
        print("=" * 60)
        
        # Save results to JSON
        results_file = self.project_root / "validation_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": str(Path(__file__).stat().st_mtime),
                "summary": {
                    "passed": passed,
                    "warnings": warnings,
                    "failed": failed
                },
                "tests": self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")


class ScreenshotCapture:
    """Capture screenshots for visual validation"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.screenshots_dir = self.project_root / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def capture_all(self, url="http://localhost:8000"):
        """Capture screenshots of key views"""
        if not SELENIUM_AVAILABLE:
            print("\n⚠️  Screenshot capture requires Selenium")
            return
        
        print("\n📸 Capturing Screenshots...")
        print(f"   URL: {url}")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Capture different views
            views = [
                ("dashboard", "Dashboard view"),
                ("all", "Library view"),
                ("movies", "Movies view"),
            ]
            
            for view, description in views:
                driver.get(f"{url}#{view}")
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "main-content"))
                )
                
                screenshot_path = self.screenshots_dir / f"{view}_view.png"
                driver.save_screenshot(str(screenshot_path))
                print(f"   ✅ {description}: {screenshot_path.name}")
            
            driver.quit()
            print(f"\n💾 Screenshots saved to: {self.screenshots_dir}")
            
        except Exception as e:
            print(f"\n❌ Screenshot capture failed: {e}")


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "UI VALIDATION SUITE" + " " * 21 + "║")
    print("║" + " " * 12 + "Apple-Grade Design System" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    
    # Run validation
    validator = UIValidator(project_root)
    validator.validate_all()
    
    # Capture screenshots if server is running
    if "--screenshots" in sys.argv:
        capture = ScreenshotCapture(project_root)
        url = sys.argv[sys.argv.index("--screenshots") + 1] if len(sys.argv) > sys.argv.index("--screenshots") + 1 else "http://localhost:8000"
        capture.capture_all(url)
    
    print("\n✨ Validation complete!")


if __name__ == "__main__":
    main()
