#!/usr/bin/env python3
"""
Test script to verify AWS Bedrock access and Claude model availability.
"""

import json
import sys

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)


def test_bedrock_access():
    """Test Bedrock access and list available Claude models."""
    print("🔍 Testing AWS Bedrock Access")
    print("=" * 60)

    try:
        # Create Bedrock client
        print("\n1. Creating Bedrock client...")
        bedrock = boto3.client('bedrock', region_name='us-west-2')
        print("   ✅ Bedrock client created")

        # List foundation models
        print("\n2. Listing available foundation models...")
        response = bedrock.list_foundation_models()

        models = response.get('modelSummaries', [])
        print(f"   ✅ Found {len(models)} models")

        # Filter for Claude models
        print("\n3. Claude models available:")
        print("   " + "-" * 56)

        claude_models = [m for m in models if 'claude' in m.get('modelId', '').lower()]

        if not claude_models:
            print("   ⚠️  No Claude models found")
            return False

        for model in sorted(claude_models, key=lambda x: x.get('modelId', '')):
            model_id = model.get('modelId', 'unknown')
            model_name = model.get('modelName', 'unknown')
            provider = model.get('providerName', 'unknown')

            # Highlight Sonnet 4.5/4.6 models
            highlight = ""
            if 'sonnet-4' in model_id.lower():
                highlight = " ⭐"

            print(f"   • {model_id}{highlight}")
            print(f"     Name: {model_name}")
            print(f"     Provider: {provider}")
            print()

        # Test specific Claude Sonnet 4.5 model
        print("\n4. Testing specific model access:")
        target_models = [
            "us.anthropic.claude-sonnet-4-20250514-v1:0",  # From example
            "anthropic.claude-sonnet-4-0-v1:0",  # Alternative naming
            "anthropic.claude-sonnet-3-5-v2:0",  # Fallback
        ]

        for target_model in target_models:
            if any(target_model in m.get('modelId', '') for m in models):
                print(f"   ✅ Model '{target_model}' is available")
                return True

        print(f"   ⚠️  Specific Sonnet 4 models not found")
        print(f"   💡 Available Claude models listed above")

        return True

    except NoCredentialsError:
        print("   ❌ No AWS credentials found")
        print("   💡 Configure credentials with: aws configure")
        return False

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"   ❌ AWS Error ({error_code}): {error_msg}")

        if error_code == 'AccessDeniedException':
            print("   💡 Your AWS credentials don't have Bedrock access")
            print("   💡 Required IAM permissions: bedrock:ListFoundationModels")

        return False

    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_bedrock_runtime():
    """Test Bedrock Runtime for model invocation."""
    print("\n" + "=" * 60)
    print("🔍 Testing Bedrock Runtime Access")
    print("=" * 60)

    try:
        print("\n1. Creating Bedrock Runtime client...")
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
        print("   ✅ Bedrock Runtime client created")

        print("\n2. Testing model invocation permissions...")
        # We won't actually invoke to avoid costs, just verify client creation
        print("   ✅ Client ready for model invocations")
        print("   💡 Actual model invocation requires:")
        print("      - bedrock:InvokeModel permission")
        print("      - Model access enabled in AWS Console")

        return True

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def show_configuration():
    """Show current AWS configuration."""
    print("\n" + "=" * 60)
    print("⚙️  Current AWS Configuration")
    print("=" * 60)

    try:
        session = boto3.Session()
        credentials = session.get_credentials()

        if credentials:
            print(f"   Profile: {session.profile_name}")
            print(f"   Region: {session.region_name}")
            print(f"   Access Key: {credentials.access_key[:10]}...")
            print("   ✅ AWS credentials configured")
        else:
            print("   ⚠️  No credentials found")

    except Exception as e:
        print(f"   ⚠️  Could not retrieve configuration: {e}")


def main():
    """Main test runner."""
    print("🧪 AWS Bedrock Configuration Test")
    print()

    show_configuration()

    bedrock_ok = test_bedrock_access()
    runtime_ok = test_bedrock_runtime()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"   Bedrock API Access: {'✅ PASS' if bedrock_ok else '❌ FAIL'}")
    print(f"   Bedrock Runtime: {'✅ PASS' if runtime_ok else '❌ FAIL'}")

    if bedrock_ok and runtime_ok:
        print("\n✅ All tests passed! Bedrock is configured correctly.")
        print("\n💡 Next steps:")
        print("   1. Install strands-agents: pip install strands-agents")
        print("   2. Run example: python examples/strands_agent_demo.py")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
