"""
Google Cloud Pub/Sub Topic Setup
Creates and manages Pub/Sub topics for ingestion pipelines.
Uses service account (sales-intel-poc-sa) for authentication.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from google.cloud import pubsub_v1
from google.api_core import exceptions
from utils.secret_manager import get_secret_client

logger = logging.getLogger(__name__)


class PubSubManager:
    """
    Manager for creating and managing Pub/Sub topics and subscriptions.
    """
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Initialize Pub/Sub manager.
        
        Args:
            project_id: GCP project ID. If not provided, uses environment or metadata.
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        if not self.project_id:
            raise ValueError("GCP project ID is required. Set GCP_PROJECT_ID environment variable.")
        
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        
        logger.info(f"Initialized Pub/Sub manager for project: {self.project_id}")
    
    def create_topic(self, topic_name: str, labels: Optional[Dict[str, str]] = None) -> pubsub_v1.types.Topic:
        """
        Create a Pub/Sub topic.
        
        Args:
            topic_name: Name of the topic
            labels: Optional labels for the topic
        
        Returns:
            Created topic object
        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        
        try:
            # Check if topic already exists
            try:
                topic = self.publisher.get_topic(request={"topic": topic_path})
                logger.info(f"Topic {topic_name} already exists")
                return topic
            except exceptions.NotFound:
                pass
            
            # Create topic
            topic_config = {}
            if labels:
                topic_config["labels"] = labels
            
            topic = self.publisher.create_topic(
                request={
                    "name": topic_path,
                    **topic_config
                }
            )
            
            logger.info(f"Successfully created topic: {topic_name}")
            return topic
            
        except exceptions.AlreadyExists:
            logger.info(f"Topic {topic_name} already exists")
            return self.publisher.get_topic(request={"topic": topic_path})
        except Exception as e:
            logger.error(f"Error creating topic {topic_name}: {e}")
            raise
    
    def create_subscription(
        self,
        subscription_name: str,
        topic_name: str,
        ack_deadline_seconds: int = 600,
        retain_acked_messages: bool = False
    ) -> pubsub_v1.types.Subscription:
        """
        Create a Pub/Sub subscription.
        
        Args:
            subscription_name: Name of the subscription
            topic_name: Name of the topic to subscribe to
            ack_deadline_seconds: Acknowledgment deadline in seconds
            retain_acked_messages: Whether to retain acknowledged messages
        
        Returns:
            Created subscription object
        """
        subscription_path = self.subscriber.subscription_path(self.project_id, subscription_name)
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        
        try:
            # Check if subscription already exists
            try:
                subscription = self.subscriber.get_subscription(
                    request={"subscription": subscription_path}
                )
                logger.info(f"Subscription {subscription_name} already exists")
                return subscription
            except exceptions.NotFound:
                pass
            
            # Create subscription
            subscription = self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path,
                    "ack_deadline_seconds": ack_deadline_seconds,
                    "retain_acked_messages": retain_acked_messages
                }
            )
            
            logger.info(f"Successfully created subscription: {subscription_name}")
            return subscription
            
        except exceptions.AlreadyExists:
            logger.info(f"Subscription {subscription_name} already exists")
            return self.subscriber.get_subscription(request={"subscription": subscription_path})
        except Exception as e:
            logger.error(f"Error creating subscription {subscription_name}: {e}")
            raise
    
    def publish_message(self, topic_name: str, data: bytes, attributes: Optional[Dict[str, str]] = None) -> str:
        """
        Publish a message to a topic.
        
        Args:
            topic_name: Name of the topic
            data: Message data as bytes
            attributes: Optional message attributes
        
        Returns:
            Message ID
        """
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        
        try:
            future = self.publisher.publish(
                topic_path,
                data,
                **attributes or {}
            )
            message_id = future.result()
            logger.info(f"Published message to {topic_name}: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Error publishing message to {topic_name}: {e}")
            raise


def setup_ingestion_topics(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Set up Pub/Sub topics for ingestion pipelines.
    
    Creates topics for:
    - Gmail ingestion
    - Salesforce ingestion
    - Dialpad ingestion
    - HubSpot ingestion
    
    Args:
        project_id: Optional GCP project ID override
    
    Returns:
        Dictionary with created topics information
    """
    manager = PubSubManager(project_id)
    
    topics_config = [
        {
            "name": "gmail-ingestion",
            "labels": {
                "environment": "production",
                "source": "gmail",
                "managed_by": "python_script"
            }
        },
        {
            "name": "salesforce-ingestion",
            "labels": {
                "environment": "production",
                "source": "salesforce",
                "managed_by": "python_script"
            }
        },
        {
            "name": "dialpad-ingestion",
            "labels": {
                "environment": "production",
                "source": "dialpad",
                "managed_by": "python_script"
            }
        },
        {
            "name": "hubspot-ingestion",
            "labels": {
                "environment": "production",
                "source": "hubspot",
                "managed_by": "python_script"
            }
        }
    ]
    
    created_topics = {}
    
    for topic_config in topics_config:
        topic_name = topic_config["name"]
        try:
            topic = manager.create_topic(topic_name, topic_config.get("labels"))
            created_topics[topic_name] = {
                "name": topic_name,
                "path": topic.name,
                "status": "created" if hasattr(topic, 'name') else "exists"
            }
        except Exception as e:
            logger.error(f"Failed to create topic {topic_name}: {e}")
            created_topics[topic_name] = {
                "name": topic_name,
                "status": "error",
                "error": str(e)
            }
    
    return created_topics


def setup_subscriptions(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Set up subscriptions for ingestion topics.
    
    Args:
        project_id: Optional GCP project ID override
    
    Returns:
        Dictionary with created subscriptions information
    """
    manager = PubSubManager(project_id)
    
    subscriptions_config = [
        {
            "name": "gmail-ingestion-sub",
            "topic": "gmail-ingestion"
        },
        {
            "name": "salesforce-ingestion-sub",
            "topic": "salesforce-ingestion"
        },
        {
            "name": "dialpad-ingestion-sub",
            "topic": "dialpad-ingestion"
        },
        {
            "name": "hubspot-ingestion-sub",
            "topic": "hubspot-ingestion"
        }
    ]
    
    created_subscriptions = {}
    
    for sub_config in subscriptions_config:
        sub_name = sub_config["name"]
        topic_name = sub_config["topic"]
        
        try:
            subscription = manager.create_subscription(sub_name, topic_name)
            created_subscriptions[sub_name] = {
                "name": sub_name,
                "topic": topic_name,
                "path": subscription.name,
                "status": "created" if hasattr(subscription, 'name') else "exists"
            }
        except Exception as e:
            logger.error(f"Failed to create subscription {sub_name}: {e}")
            created_subscriptions[sub_name] = {
                "name": sub_name,
                "topic": topic_name,
                "status": "error",
                "error": str(e)
            }
    
    return created_subscriptions


def example_publish_message():
    """
    Example: Publish a test message to a topic.
    """
    manager = PubSubManager()
    
    # Publish test message to Gmail ingestion topic
    import json
    test_data = {
        "source": "gmail",
        "action": "sync",
        "mailbox": "test@example.com"
    }
    
    message_id = manager.publish_message(
        "gmail-ingestion",
        json.dumps(test_data).encode('utf-8'),
        attributes={"source": "gmail", "type": "test"}
    )
    
    print(f"Published test message: {message_id}")


def main():
    """
    Main function to set up all Pub/Sub topics and subscriptions.
    """
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Setting up Pub/Sub Topics for Ingestion Pipelines")
    print("=" * 60)
    
    # Set up topics
    print("\n1. Creating topics...")
    topics = setup_ingestion_topics()
    
    for topic_name, info in topics.items():
        status = info.get("status", "unknown")
        print(f"  {topic_name}: {status}")
        if status == "error":
            print(f"    Error: {info.get('error', 'Unknown error')}")
    
    # Set up subscriptions
    print("\n2. Creating subscriptions...")
    subscriptions = setup_subscriptions()
    
    for sub_name, info in subscriptions.items():
        status = info.get("status", "unknown")
        print(f"  {sub_name} -> {info.get('topic', 'N/A')}: {status}")
        if status == "error":
            print(f"    Error: {info.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("Pub/Sub setup completed!")
    print("=" * 60)
    
    # Example: Publish test message
    # print("\n3. Publishing test message...")
    # example_publish_message()


if __name__ == "__main__":
    main()

