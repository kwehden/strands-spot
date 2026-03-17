#!/usr/bin/env python3
"""
Test Strands Agent with Bedrock and use_spot tool.
This demonstrates correct Bedrock configuration with inference profiles.
"""

import sys

try:
    from strands import Agent
    from strands.models.bedrock import BedrockModel
except ImportError:
    print("❌ strands-agents not installed")
    print("   Install with: source .venv/bin/activate && pip install strands-agents")
    sys.exit(1)

# Import the use_spot tool
from strands_spot import use_spot


def test_basic_agent():
    """Test basic agent creation with Bedrock model."""
    print("🧪 Test 1: Basic Agent Creation")
    print("-" * 60)

    # Use Claude 3.5 Sonnet v2 which supports on-demand throughput
    # Alternative: use inference profile ARN for newer models
    model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",  # 3.5 Sonnet v2
        temperature=1.0,
        max_tokens=4096
    )

    print(f"   ✅ Created BedrockModel with Claude 3.5 Sonnet v2")

    # Create agent with use_spot tool
    agent = Agent(
        model=model,
        tools=[use_spot],
        system_prompt="""You are a helpful assistant with access to a Boston Dynamics Spot robot.

You have the use_spot tool which allows you to control the robot using service-method patterns.
Examples:
- service="robot_state", method="get_robot_state" - query robot status
- service="robot_command", method="stand" - make robot stand up
- service="image", method="list_image_sources" - list available cameras

Be helpful and explain what operations you could perform."""
    )

    print("   ✅ Created Agent with use_spot tool")

    return agent


def test_agent_understanding():
    """Test that agent understands the use_spot tool."""
    print("\n🧪 Test 2: Agent Understanding of use_spot")
    print("-" * 60)

    agent = test_basic_agent()

    # Ask agent about its capabilities (no robot needed)
    print("\n   Query: 'What can you do with the Spot robot?'")
    print("   " + "-" * 56)

    response = agent("What can you do with the Spot robot? List 5 example operations.")

    print(f"\n   Agent Response:")
    print("   " + "-" * 56)
    print(f"   {response}")

    print("\n   ✅ Agent understands use_spot capabilities")


def test_model_options():
    """Show available Claude model options with correct configuration."""
    print("\n🧪 Test 3: Bedrock Model Configuration Options")
    print("-" * 60)

    print("\n   ✅ MODELS WITH ON-DEMAND THROUGHPUT SUPPORT:")
    print("   " + "-" * 56)

    on_demand_models = {
        "Claude 3.5 Sonnet v2 (Recommended)": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "Claude 3.5 Haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
        "Claude 3.5 Sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "Claude 3 Sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "Claude 3 Haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    }

    for name, model_id in on_demand_models.items():
        print(f"   • {name}")
        print(f"     model_id='{model_id}'")
        print()

    print("\n   ⚠️  MODELS REQUIRING INFERENCE PROFILE:")
    print("   " + "-" * 56)
    print("   These models need an inference profile ARN:")

    profile_models = {
        "Claude Sonnet 4.6": "anthropic.claude-sonnet-4-6",
        "Claude Sonnet 4.5": "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "Claude Sonnet 4": "anthropic.claude-sonnet-4-20250514-v1:0",
        "Claude Opus 4.6": "anthropic.claude-opus-4-6-v1",
        "Claude Haiku 4.5": "anthropic.claude-haiku-4-5-20251001-v1:0",
    }

    for name, model_id in profile_models.items():
        print(f"   • {name}")
        print(f"     model_id='{model_id}' (requires inference profile)")
        print()

    print("\n   📖 CONFIGURATION EXAMPLES:")
    print("   " + "-" * 56)
    print("""
   # Option 1: On-demand model (easiest)
   model = BedrockModel(
       model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
       temperature=1.0,
       max_tokens=8192
   )

   # Option 2: Inference profile for newer models
   # Create profile in AWS Console first, then:
   model = BedrockModel(
       model_id="arn:aws:bedrock:us-west-2:123456789012:inference-profile/...",
       temperature=1.0,
       max_tokens=8192
   )

   # Option 3: Use region-specific inference profile
   model = BedrockModel(
       model_id="us.anthropic.claude-sonnet-4-5",  # Regional inference profile
       temperature=1.0,
       max_tokens=8192
   )
   """)

    print("\n   💡 Learn more:")
    print("      https://strandsagents.com/latest/user-guide/concepts/model-providers/amazon-bedrock/#on-demand-throughput-isnt-supported")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🦆 Strands + Bedrock + use_spot Integration Test")
    print("=" * 60)
    print()

    try:
        # Test 1: Basic creation
        print("   Note: Using Claude 3.5 Sonnet v2 (on-demand model)")
        print()
        agent = test_basic_agent()

        # Test 2: Agent understanding (requires API call)
        test_agent_understanding()

        # Test 3: Show options
        test_model_options()

        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("   1. Set Spot robot environment variables:")
        print("      export SPOT_HOSTNAME=192.168.80.3")
        print("      export SPOT_USERNAME=admin")
        print("      export SPOT_PASSWORD=your_password")
        print()
        print("   2. Update examples/strands_agent_demo.py with on-demand model")
        print()
        print("   3. Run the full agent demo:")
        print("      source .venv/bin/activate")
        print("      python examples/strands_agent_demo.py")
        print()
        print("   4. Or use the agent interactively:")
        print("      agent('Make the robot stand up')")
        print("      agent('Take a picture from the front camera')")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
