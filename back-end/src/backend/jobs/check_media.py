from sqlmodel import Session, select
from backend.db import engine
from backend.models import SubscriptionRequest, SubscriptionStatus, Notification
from backend.services.emby import emby_client
import logging

logger = logging.getLogger(__name__)

async def check_new_media_job():
    logger.info("Starting check_new_media_job")
    with Session(engine) as session:
        # Get all approved requests
        statement = select(SubscriptionRequest).where(SubscriptionRequest.status == SubscriptionStatus.APPROVED)
        requests = session.exec(statement).all()
        
        if not requests:
            return

        for request in requests:
            # Check Emby
            # We use search_by_provider_id with tmdb
            # Emby items might have ProviderIds: { "Tmdb": "12345" }
            try:
                items = await emby_client.search_by_provider_id("Tmdb", request.tmdb_id)
                if items:
                    # Found it!
                    request.status = SubscriptionStatus.COMPLETED
                    session.add(request)
                    
                    # Create Notification
                    notification = Notification(
                        user_id=request.user_id,
                        title="资源已入库",
                        message=f"您申请的 '{request.title}' 已经入库 Emby，现在可以观看了。",
                        related_subscription_id=request.id
                    )
                    session.add(notification)
                    session.commit()
                    logger.info(f"Request {request.id} completed and notification sent.")
            except Exception as e:
                logger.error(f"Error checking media for request {request.id}: {e}")

