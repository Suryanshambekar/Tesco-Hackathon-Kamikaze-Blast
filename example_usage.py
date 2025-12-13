"""
Example usage of TESCORA.AI backend
"""
from pathlib import Path
from backend.service import TescoraService
from backend.api import process_creative_api

def example_basic_usage():
    """Basic example of processing a creative"""
    
    # Initialize service
    service = TescoraService()
    
    # Example paths (update these to your actual image paths)
    packshot_path = Path("uploads/packshot.jpg")
    background_path = Path("uploads/background.jpg")
    logo_path = Path("uploads/logo.png")
    
    # Check if files exist (for demo purposes)
    if not packshot_path.exists():
        print(f"Please add a packshot image at: {packshot_path}")
        return
    
    # Process creative
    print("Processing creative...")
    results = service.process_creative(
        packshot_path=packshot_path,
        background_path=background_path if background_path.exists() else None,
        headline="Amazing Product",
        price="£9.99",
        claim="Save 20% Today!",
        logo_path=logo_path if logo_path.exists() else None,
        formats=["1:1", "4:5", "9:16"],
        run_compliance=True
    )
    
    # Display results
    print("\n=== Processing Results ===")
    print(f"Success: {results['success']}")
    
    if results['success']:
        print("\n=== Exports ===")
        for format_name, export_result in results['exports'].items():
            if export_result.get('success'):
                print(f"\n{format_name}:")
                print(f"  Path: {export_result['path']}")
                print(f"  Size: {export_result['size_kb']} KB")
                print(f"  Dimensions: {export_result['dimensions']}")
        
        if results.get('compliance'):
            print("\n=== Compliance Results ===")
            for format_name, compliance in results['compliance'].items():
                print(f"\n{format_name}:")
                print(f"  Compliant: {compliance['is_compliant']}")
                print(f"  Risk Level: {compliance['risk_level']}")
                if compliance.get('issues'):
                    print(f"  Issues: {len(compliance['issues'])}")
                    for issue in compliance['issues']:
                        print(f"    - {issue['type']}: {issue['message']}")
    else:
        print(f"\nErrors: {results.get('errors', [])}")


def example_api_usage():
    """Example using the API layer"""
    
    packshot_path = "uploads/packshot.jpg"
    
    print("Using API layer...")
    results = process_creative_api(
        packshot_path=packshot_path,
        headline="Special Offer",
        price="£12.99",
        claim="Limited Time Only",
        formats=["1:1", "9:16"]
    )
    
    print(f"Success: {results['success']}")


def example_preview():
    """Example of generating a preview"""
    
    service = TescoraService()
    packshot_path = Path("uploads/packshot.jpg")
    
    if not packshot_path.exists():
        print(f"Please add a packshot image at: {packshot_path}")
        return
    
    print("Generating preview...")
    preview = service.preview_layout(
        format_name="1:1",
        packshot_path=packshot_path,
        headline="Preview Product",
        price="£9.99"
    )
    
    # Save preview
    preview_path = Path("outputs/preview.jpg")
    preview.save(preview_path)
    print(f"Preview saved to: {preview_path}")


if __name__ == "__main__":
    print("TESCORA.AI Backend - Example Usage\n")
    print("Choose an example:")
    print("1. Basic usage")
    print("2. API usage")
    print("3. Preview generation")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_api_usage()
    elif choice == "3":
        example_preview()
    else:
        print("Invalid choice")

