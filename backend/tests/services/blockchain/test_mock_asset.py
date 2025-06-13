import asyncio
import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.blockchain.asset.base import AssetProvider
from backend.app.services.blockchain.asset.mock_provider import MockAssetProvider
from backend.app.services.blockchain.errors import TemporaryBlockchainError, PermanentBlockchainError

@pytest.fixture
def asset_provider():
    provider = MockAssetProvider()
    # Set delay to 0 for faster tests
    provider.simulated_delay = 0
    return provider

@pytest.mark.asyncio
async def test_create_asset_success(asset_provider):
    # Test successful asset creation
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 1,
        "attributes": {
            "strength": 10,
            "agility": 8,
            "intelligence": 5
        }
    }
    
    result = await asset_provider.create_asset(owner_address, metadata)
    
    assert "asset_id" in result
    assert result["owner_address"] == owner_address
    assert result["metadata"] == metadata
    assert "created_at" in result
    assert "transaction_id" in result

@pytest.mark.asyncio
async def test_create_asset_no_metadata(asset_provider):
    # Test asset creation with no metadata
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    metadata = {}
    
    with pytest.raises(PermanentBlockchainError):
        await asset_provider.create_asset(owner_address, metadata)

@pytest.mark.asyncio
async def test_create_asset_network_error(asset_provider):
    # Test asset creation with network error
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 1
    }
    
    # Set failure rate to 100% to simulate network error
    asset_provider.failure_rate = 1.0
    
    with pytest.raises(TemporaryBlockchainError):
        await asset_provider.create_asset(owner_address, metadata)
    
    # Reset failure rate for other tests
    asset_provider.failure_rate = 0.0

@pytest.mark.asyncio
async def test_transfer_asset_success(asset_provider):
    # First create an asset
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    new_owner_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 1
    }
    
    create_result = await asset_provider.create_asset(owner_address, metadata)
    asset_id = create_result["asset_id"]
    
    # Then transfer it
    transfer_result = await asset_provider.transfer_asset(asset_id, owner_address, new_owner_address)
    
    assert transfer_result["success"] is True
    assert transfer_result["asset_id"] == asset_id
    assert transfer_result["from_address"] == owner_address
    assert transfer_result["to_address"] == new_owner_address
    assert "transaction_id" in transfer_result
    assert "timestamp" in transfer_result
    
    # Verify ownership changed
    assets = await asset_provider.get_assets(new_owner_address)
    assert len(assets) == 1
    assert assets[0]["asset_id"] == asset_id

@pytest.mark.asyncio
async def test_transfer_asset_not_owner(asset_provider):
    # First create an asset
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    wrong_address = "0xwrongaddress"
    new_owner_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 1
    }
    
    create_result = await asset_provider.create_asset(owner_address, metadata)
    asset_id = create_result["asset_id"]
    
    # Try to transfer from wrong address
    with pytest.raises(PermanentBlockchainError):
        await asset_provider.transfer_asset(asset_id, wrong_address, new_owner_address)

@pytest.mark.asyncio
async def test_get_assets(asset_provider):
    # Create multiple assets for a wallet
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    
    # Create 3 assets
    for i in range(3):
        await asset_provider.create_asset(
            owner_address, 
            {
                "name": f"Test Character {i}",
                "type": "Warrior",
                "level": i + 1
            }
        )
    
    # Get assets
    assets = await asset_provider.get_assets(owner_address)
    
    assert len(assets) == 3
    for asset in assets:
        assert "asset_id" in asset
        assert asset["owner_address"] == owner_address
        assert "metadata" in asset
        assert "created_at" in asset

@pytest.mark.asyncio
async def test_get_assets_no_assets(asset_provider):
    # Test getting assets for a wallet with no assets
    owner_address = "0xemptywallet"
    
    assets = await asset_provider.get_assets(owner_address)
    
    assert len(assets) == 0

@pytest.mark.asyncio
async def test_update_asset_metadata_success(asset_provider):
    # First create an asset
    owner_address = "0x1234567890abcdef1234567890abcdef12345678"
    metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 1,
        "attributes": {
            "strength": 10,
            "agility": 8
        }
    }
    
    create_result = await asset_provider.create_asset(owner_address, metadata)
    asset_id = create_result["asset_id"]
    
    # Then update its metadata
    new_metadata = {
        "level": 2,
        "attributes": {
            "strength": 12
        }
    }
    
    update_result = await asset_provider.update_asset_metadata(asset_id, new_metadata)
    
    assert update_result["asset_id"] == asset_id
    assert update_result["owner_address"] == owner_address
    assert "updated_at" in update_result
    assert "transaction_id" in update_result
    
    # Verify metadata was merged correctly
    expected_metadata = {
        "name": "Test Character",
        "type": "Warrior",
        "level": 2,  # Updated
        "attributes": {
            "strength": 12,  # Updated
            "agility": 8
        }
    }
    assert update_result["metadata"] == expected_metadata

@pytest.mark.asyncio
async def test_update_asset_metadata_nonexistent(asset_provider):
    # Test updating metadata for a nonexistent asset
    asset_id = "nonexistent-asset-id"
    metadata = {
        "level": 2
    }
    
    with pytest.raises(PermanentBlockchainError):
        await asset_provider.update_asset_metadata(asset_id, metadata)
