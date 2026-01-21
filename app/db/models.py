# app/db/models.py
from sqlalchemy import (
    Integer, String, Text, DateTime, Float, ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeedInfo(Base):
    __tablename__ = "feed_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    last_build_date: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    fetch_history: Mapped[list["FetchHistory"]] = relationship(
        "FetchHistory", back_populates="feed", cascade="all, delete-orphan"
    )


class FetchHistory(Base):
    __tablename__ = "fetch_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(Integer, ForeignKey("feed_info.id"))
    fetch_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    quotes_added: Mapped[int] = mapped_column(Integer, default=0)
    duplicates_skipped: Mapped[int] = mapped_column(Integer, default=0)
    total_processed: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str | None] = mapped_column(Text)

    # Relationships
    feed: Mapped["FeedInfo"] = relationship("FeedInfo", back_populates="fetch_history")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author: Mapped[str | None] = mapped_column(Text)
    quote_text: Mapped[str] = mapped_column(Text, nullable=False)
    guid: Mapped[str | None] = mapped_column(Text)
    pub_date: Mapped[str | None] = mapped_column(Text)
    link: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    classifications: Mapped[list["QuoteClassification"]] = relationship(
        "QuoteClassification", back_populates="quote", cascade="all, delete-orphan"
    )
    images: Mapped[list["QuoteImage"]] = relationship(
        "QuoteImage", back_populates="quote", cascade="all, delete-orphan"
    )
    telegram_uploads: Mapped[list["TelegramUpload"]] = relationship(
        "TelegramUpload", back_populates="quote", cascade="all, delete-orphan"
    )


class QuoteClassification(Base):
    __tablename__ = "quote_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    reasoning: Mapped[str | None] = mapped_column(Text)
    classified_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    quote: Mapped["Quote"] = relationship("Quote", back_populates="classifications")


class QuoteImage(Base):
    __tablename__ = "quote_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    quote: Mapped["Quote"] = relationship("Quote", back_populates="images")


class TelegramUpload(Base):
    __tablename__ = "telegram_uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[int] = mapped_column(Integer, ForeignKey("quotes.id"), nullable=False)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    message_id: Mapped[int | None] = mapped_column(Integer)
    uploaded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    quote: Mapped["Quote"] = relationship("Quote", back_populates="telegram_uploads")
