# Blockchain Abstraction Layer Tasks

This document breaks down the implementation tasks for strengthening the blockchain abstraction layer in the Coin Clash project, following the incremental migration approach.

## Table of Contents
- [1. Interface Definition](#1-interface-definition)
- [2. Mock Implementation](#2-mock-implementation)
- [3. Core Integration](#3-core-integration)
- [4. Testing and Validation](#4-testing-and-validation)
- [5. Documentation](#5-documentation)

## 1. Interface Definition

### 1.1 Wallet Interface
- [ ] **Task**: Define wallet interface contract
- **Files/Modules**:
  - `/backend/app/services/blockchain/wallet/base.py` - Base wallet interface
- **Code Example**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, Optional, List

  class WalletProvider(ABC):
      @abstractmethod
      async def connect_wallet(self, wallet_address: str, chain_id: str) -> Dict:
          """Connect to a wallet."""
          pass
      
      @abstractmethod
      async def disconnect_wallet(self, wallet_address: str) -> Dict:
          """Disconnect from a wallet."""
          pass
      
      @abstractmethod
      async def verify_signature(self, wallet_address: str, message: str, signature: str) -> bool:
          """Verify a signature from a wallet."""
          pass
      
      @abstractmethod
      async def get_supported_chains(self) -> List[Dict]:
          """Get list of supported blockchain networks."""
          pass
  ```

### 1.2 Payment Interface
- [ ] **Task**: Define payment interface contract
- **Files/Modules**:
  - `/backend/app/services/blockchain/payment/base.py` - Base payment interface
- **Code Example**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, Optional, List
  
  class PaymentProvider(ABC):
      @abstractmethod
      async def process_deposit(self, wallet_address: str, amount: float, currency: str) -> Dict:
          """Process a deposit from a wallet."""
          pass
      
      @abstractmethod
      async def process_withdrawal(self, wallet_address: str, amount: float, currency: str) -> Dict:
          """Process a withdrawal to a wallet."""
          pass
      
      @abstractmethod
      async def get_balance(self, wallet_address: str, currency: str) -> float:
          """Get the balance for a wallet."""
          pass
      
      @abstractmethod
      async def estimate_fees(self, amount: float, currency: str) -> Dict:
          """Estimate transaction fees."""
          pass
  ```

### 1.3 Transaction Interface
- [ ] **Task**: Define transaction interface contract
- **Files/Modules**:
  - `/backend/app/services/blockchain/transaction/base.py` - Base transaction interface
- **Code Example**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, Optional, List
  
  class TransactionProvider(ABC):
      @abstractmethod
      async def create_transaction(self, from_address: str, to_address: str, amount: float, currency: str) -> Dict:
          """Create a new blockchain transaction."""
          pass
      
      @abstractmethod
      async def get_transaction_status(self, transaction_id: str) -> Dict:
          """Get the status of a transaction."""
          pass
      
      @abstractmethod
      async def get_transaction_history(self, wallet_address: str, limit: int = 10) -> List[Dict]:
          """Get transaction history for a wallet."""
          pass
      
      @abstractmethod
      async def retry_transaction(self, transaction_id: str) -> Dict:
          """Retry a failed transaction."""
          pass
  ```

### 1.4 Asset Interface
- [ ] **Task**: Define asset interface contract
- **Files/Modules**:
  - `/backend/app/services/blockchain/asset/base.py` - Base asset interface
- **Code Example**:
  ```python
  from abc import ABC, abstractmethod
  from typing import Dict, Optional, List
  
  class AssetProvider(ABC):
      @abstractmethod
      async def create_asset(self, owner_address: str, metadata: Dict) -> Dict:
          """Create a new asset."""
          pass
      
      @abstractmethod
      async def transfer_asset(self, asset_id: str, from_address: str, to_address: str) -> Dict:
          """Transfer an asset to a new owner."""
          pass
      
      @abstractmethod
      async def get_assets(self, owner_address: str) -> List[Dict]:
          """Get assets owned by an address."""
          pass
      
      @abstractmethod
      async def update_asset_metadata(self, asset_id: str, metadata: Dict) -> Dict:
          """Update asset metadata."""
          pass
  ```

### 1.5 Error Handling Framework
- [ ] **Task**: Define error handling framework for blockchain operations
- **Files/Modules**:
  - `/backend/app/services/blockchain/errors.py` - Blockchain error classes
- **Code Example**:
  ```python
  from enum import Enum
  
  class BlockchainErrorType(Enum):
      TEMPORARY = "temporary"  # Network issues, timeouts
      PERMANENT = "permanent"  # Invalid addresses, insufficient funds
      UNKNOWN = "unknown"      # Unexpected errors
  
  class BlockchainError(Exception):
      def __init__(self, message: str, error_type: BlockchainErrorType, retry_allowed: bool = True):
          self.message = message
          self.error_type = error_type
          self.retry_allowed = retry_allowed
          super().__init__(self.message)
  
  class TemporaryBlockchainError(BlockchainError):
      def __init__(self, message: str):
          super().__init__(message, BlockchainErrorType.TEMPORARY, True)
  
  class PermanentBlockchainError(BlockchainError):
      def __init__(self, message: str):
          super().__init__(message, BlockchainErrorType.PERMANENT, False)
  
  class UnknownBlockchainError(BlockchainError):
      def __init__(self, message: str):
          super().__init__(message, BlockchainErrorType.UNKNOWN, True)
  ```

## 2. Mock Implementation

### 2.1 Mock Wallet Provider
- [ ] **Task**: Implement mock wallet provider
- **Files/Modules**:
  - `/backend/app/services/blockchain/wallet/mock_provider.py` - Mock wallet implementation
- **Functionality**:
  - Store wallet addresses and chain IDs in memory
  - Simulate wallet connection and disconnection
  - Verify mock signatures
  - Support multiple mock chains

### 2.2 Mock Payment Provider
- [ ] **Task**: Implement mock payment provider
- **Files/Modules**:
  - `/backend/app/services/blockchain/payment/mock_provider.py` - Mock payment implementation
- **Functionality**:
  - Track balances in memory
  - Process mock deposits and withdrawals
  - Simulate transaction delays
  - Generate mock transaction receipts

### 2.3 Mock Transaction Provider
- [ ] **Task**: Implement mock transaction provider
- **Files/Modules**:
  - `/backend/app/services/blockchain/transaction/mock_provider.py` - Mock transaction implementation
- **Functionality**:
  - Generate mock transaction IDs
  - Track transaction status in memory
  - Simulate transaction lifecycle (pending, confirmed, failed)
  - Provide configurable success/failure scenarios

### 2.4 Mock Asset Provider
- [ ] **Task**: Implement mock asset provider
- **Files/Modules**:
  - `/backend/app/services/blockchain/asset/mock_provider.py` - Mock asset implementation
- **Functionality**:
  - Create and track mock assets in memory
  - Simulate asset transfers
  - Store and retrieve mock metadata
  - Generate mock asset events

### 2.5 Retry Mechanism
- [ ] **Task**: Implement retry mechanism for blockchain operations
- **Files/Modules**:
  - `/backend/app/services/blockchain/retry.py` - Retry utilities
- **Code Example**:
  ```python
  import asyncio
  from typing import Callable, Any, Dict, Optional
  from .errors import BlockchainError, TemporaryBlockchainError
  
  async def retry_async_operation(
      operation: Callable,
      max_attempts: int = 3,
      initial_delay: float = 1.0,
      backoff_factor: float = 2.0,
      **kwargs
  ) -> Any:
      """Retry an async operation with exponential backoff."""
      attempt = 0
      delay = initial_delay
      
      while attempt < max_attempts:
          try:
              return await operation(**kwargs)
          except TemporaryBlockchainError as e:
              attempt += 1
              if attempt >= max_attempts:
                  raise
              
              await asyncio.sleep(delay)
              delay *= backoff_factor
          except BlockchainError as e:
              if not e.retry_allowed:
                  raise
              
              attempt += 1
              if attempt >= max_attempts:
                  raise
              
              await asyncio.sleep(delay)
              delay *= backoff_factor
  ```

## 3. Core Integration

### 3.1 Blockchain Service Factory
- [ ] **Task**: Implement blockchain service factory
- **Files/Modules**:
  - `/backend/app/services/blockchain/factory.py` - Blockchain service factory
- **Code Example**:
  ```python
  from typing import Dict, Type
  from .wallet.base import WalletProvider
  from .payment.base import PaymentProvider
  from .transaction.base import TransactionProvider
  from .asset.base import AssetProvider
  
  from .wallet.mock_provider import MockWalletProvider
  from .payment.mock_provider import MockPaymentProvider
  from .transaction.mock_provider import MockTransactionProvider
  from .asset.mock_provider import MockAssetProvider
  
  class BlockchainServiceFactory:
      @staticmethod
      def get_wallet_provider(provider_type: str = "mock") -> WalletProvider:
          providers: Dict[str, Type[WalletProvider]] = {
              "mock": MockWalletProvider,
              # Add real providers in Phase 3
          }
          
          if provider_type not in providers:
              raise ValueError(f"Unsupported wallet provider type: {provider_type}")
          
          return providers[provider_type]()
      
      @staticmethod
      def get_payment_provider(provider_type: str = "mock") -> PaymentProvider:
          providers: Dict[str, Type[PaymentProvider]] = {
              "mock": MockPaymentProvider,
              # Add real providers in Phase 3
          }
          
          if provider_type not in providers:
              raise ValueError(f"Unsupported payment provider type: {provider_type}")
          
          return providers[provider_type]()
      
      # Similar methods for transaction and asset providers
  ```

### 3.2 Player Service Integration
- [ ] **Task**: Integrate blockchain abstractions with player service
- **Files/Modules**:
  - `/backend/app/services/player_service.py` - Update player service
- **Changes**:
  - Add wallet association methods
  - Integrate with wallet provider
  - Update player creation and retrieval to support wallet addresses

### 3.3 Match Service Integration
- [ ] **Task**: Integrate blockchain abstractions with match service
- **Files/Modules**:
  - `/backend/app/services/match_service.py` - Update match service
- **Changes**:
  - Add payment processing for match entry
  - Integrate with payment provider
  - Update match settlement to use transaction provider

### 3.4 Character Service Integration
- [ ] **Task**: Integrate blockchain abstractions with character service
- **Files/Modules**:
  - `/backend/app/services/character_service.py` - Update character service
- **Changes**:
  - Add asset integration for characters
  - Integrate with asset provider
  - Update character lifecycle management

### 3.5 Transaction Monitoring Service
- [ ] **Task**: Implement transaction monitoring service
- **Files/Modules**:
  - `/backend/app/services/blockchain/monitor.py` - Transaction monitoring service
- **Functionality**:
  - Background task for monitoring transaction status
  - Webhook handler for transaction updates
  - Status update and notification system

## 4. Testing and Validation

### 4.1 Unit Tests for Interfaces
- [ ] **Task**: Implement unit tests for blockchain interfaces
- **Files/Modules**:
  - `/backend/tests/services/blockchain/test_wallet.py` - Wallet interface tests
  - `/backend/tests/services/blockchain/test_payment.py` - Payment interface tests
  - `/backend/tests/services/blockchain/test_transaction.py` - Transaction interface tests
  - `/backend/tests/services/blockchain/test_asset.py` - Asset interface tests

### 4.2 Mock Provider Tests
- [ ] **Task**: Implement tests for mock providers
- **Files/Modules**:
  - `/backend/tests/services/blockchain/test_mock_wallet.py` - Mock wallet tests
  - `/backend/tests/services/blockchain/test_mock_payment.py` - Mock payment tests
  - `/backend/tests/services/blockchain/test_mock_transaction.py` - Mock transaction tests
  - `/backend/tests/services/blockchain/test_mock_asset.py` - Mock asset tests

### 4.3 Integration Tests
- [ ] **Task**: Implement integration tests for blockchain services
- **Files/Modules**:
  - `/backend/tests/integration/test_blockchain_integration.py` - Integration tests
- **Functionality**:
  - Test interaction between services and blockchain providers
  - Test error handling and recovery
  - Test state management and consistency

### 4.4 Simulation Tests
- [ ] **Task**: Implement simulation tests for blockchain scenarios
- **Files/Modules**:
  - `/backend/tests/simulation/test_blockchain_scenarios.py` - Simulation tests
- **Functionality**:
  - Test network issues and timeouts
  - Test transaction failures and retries
  - Test concurrent operations

## 5. Documentation

### 5.1 API Documentation
- [ ] **Task**: Update API documentation for blockchain endpoints
- **Files/Modules**:
  - `/backend/app/api/api_v1/endpoints/wallets.py` - Wallet endpoints
  - `/backend/app/api/api_v1/endpoints/transactions.py` - Transaction endpoints

### 5.2 Interface Documentation
- [ ] **Task**: Create comprehensive documentation for blockchain interfaces
- **Files/Modules**:
  - `/docs/blockchain_interfaces.md` - Interface documentation
- **Content**:
  - Interface contracts and expected behaviors
  - Error handling and recovery
  - Usage examples

### 5.3 Mock Provider Documentation
- [ ] **Task**: Create documentation for mock providers
- **Files/Modules**:
  - `/docs/mock_providers.md` - Mock provider documentation
- **Content**:
  - Configuration options
  - Simulated behaviors
  - Testing utilities

### 5.4 README Update
- [ ] **Task**: Update README.md with blockchain abstraction layer information
- **Files/Modules**:
  - `/README.md` - Project README
- **Changes**:
  - Add blockchain abstraction layer section
  - Update project structure
  - Update development roadmap
  - Add setup instructions for blockchain testing

### 5.5 Ongoing Documentation Maintenance
- [ ] **Task**: Establish process for ongoing documentation updates
- **Responsibility**:
  - Update README.md whenever new features, dependencies, or setup steps change
  - Update API documentation when endpoints are added or modified
  - Update interface documentation when contracts change
  - Document new flows or features as they are added