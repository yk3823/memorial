"""
Hebrew Calendar service for Memorial Website.
Provides Hebrew calendar integration, date conversions, and yahrzeit calculations.
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum

import aiohttp
from pydantic import BaseModel, Field, validator

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HebrewMonth(Enum):
    """Hebrew month names."""
    TISHREI = "Tishrei"
    CHESHVAN = "Cheshvan"
    KISLEV = "Kislev"
    TEVET = "Tevet"
    SHEVAT = "Shevat"
    ADAR = "Adar"
    ADAR_II = "Adar II"
    NISSAN = "Nissan"
    IYAR = "Iyar"
    SIVAN = "Sivan"
    TAMUZ = "Tamuz"
    AV = "Av"
    ELUL = "Elul"


@dataclass
class HebrewDate:
    """
    Hebrew date representation.
    
    Attributes:
        day: Day of month (1-30)
        month: Hebrew month
        year: Hebrew year
        formatted: Formatted Hebrew date string
        is_leap_year: Whether this is a leap year
        days_in_month: Number of days in this month
    """
    day: int
    month: HebrewMonth
    year: int
    formatted: str
    is_leap_year: bool = False
    days_in_month: int = 30
    
    def __str__(self) -> str:
        return self.formatted
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "day": self.day,
            "month": self.month.value,
            "year": self.year,
            "formatted": self.formatted,
            "is_leap_year": self.is_leap_year,
            "days_in_month": self.days_in_month
        }
    
    @classmethod
    def from_string(cls, date_string: str) -> "HebrewDate":
        """
        Parse Hebrew date from string format.
        
        Args:
            date_string: Hebrew date in various formats
            
        Returns:
            HebrewDate: Parsed Hebrew date
            
        Raises:
            ValueError: If date string cannot be parsed
        """
        # This is a simplified parser - in production would need more robust parsing
        parts = date_string.split()
        if len(parts) >= 3:
            try:
                day = int(parts[0])
                month_name = parts[1]
                year = int(parts[2])
                
                # Find matching month
                month = None
                for heb_month in HebrewMonth:
                    if heb_month.value.lower() == month_name.lower():
                        month = heb_month
                        break
                
                if not month:
                    raise ValueError(f"Unknown Hebrew month: {month_name}")
                
                return cls(
                    day=day,
                    month=month,
                    year=year,
                    formatted=date_string,
                    is_leap_year=cls._is_hebrew_leap_year(year)
                )
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid Hebrew date format: {date_string}") from e
        
        raise ValueError(f"Invalid Hebrew date format: {date_string}")
    
    @staticmethod
    def _is_hebrew_leap_year(year: int) -> bool:
        """
        Check if Hebrew year is a leap year.
        
        Args:
            year: Hebrew year
            
        Returns:
            bool: True if leap year
        """
        # Hebrew leap year calculation: 7 leap years every 19 years
        # Leap years are: 3, 6, 8, 11, 14, 17, 19 in each 19-year cycle
        cycle_year = year % 19
        return cycle_year in [3, 6, 8, 11, 14, 17, 0]  # 0 = 19


class DateConversionError(Exception):
    """Exception raised when date conversion fails."""
    pass


class HebrewCalendarService:
    """
    Hebrew Calendar service providing date conversions and yahrzeit calculations.
    
    This service integrates with the HebCal API for accurate Hebrew date conversions
    and provides utilities for calculating yahrzeit dates.
    """
    
    def __init__(self):
        self.base_url = "https://www.hebcal.com/converter"
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_cache_key(self, *args) -> str:
        """Generate cache key from arguments."""
        return "|".join(str(arg) for arg in args)
    
    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache entry is still valid."""
        return (datetime.now().timestamp() - timestamp) < self._cache_ttl
    
    async def _make_api_request(
        self,
        params: Dict[str, Union[str, int]]
    ) -> Dict[str, Any]:
        """
        Make API request to HebCal service.
        
        Args:
            params: Request parameters
            
        Returns:
            dict: API response data
            
        Raises:
            DateConversionError: If API request fails
        """
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
        
        try:
            async with self.session.get(
                self.base_url,
                params={**params, "cfg": "json", "strict": "1"}
            ) as response:
                if response.status != 200:
                    raise DateConversionError(
                        f"HebCal API returned status {response.status}"
                    )
                
                data = await response.json()
                
                if "error" in data:
                    raise DateConversionError(f"HebCal API error: {data['error']}")
                
                return data
        
        except aiohttp.ClientError as e:
            logger.error(f"HebCal API request failed: {e}")
            raise DateConversionError(f"Failed to connect to Hebrew calendar service: {e}") from e
    
    async def gregorian_to_hebrew(
        self,
        gregorian_date: Union[date, datetime]
    ) -> HebrewDate:
        """
        Convert Gregorian date to Hebrew date.
        
        Args:
            gregorian_date: Gregorian date to convert
            
        Returns:
            HebrewDate: Corresponding Hebrew date
            
        Raises:
            DateConversionError: If conversion fails
        """
        if isinstance(gregorian_date, datetime):
            gregorian_date = gregorian_date.date()
        
        cache_key = f"g2h_{gregorian_date.isoformat()}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return cached_data
        
        try:
            # Make API request
            params = {
                "gd": gregorian_date.day,
                "gm": gregorian_date.month,
                "gy": gregorian_date.year,
                "g2h": "1"
            }
            
            data = await self._make_api_request(params)
            
            # Parse response
            hebrew_date = HebrewDate(
                day=int(data["hd"]),
                month=HebrewMonth(data["hm"]),
                year=int(data["hy"]),
                formatted=data["hebrew"],
                is_leap_year=HebrewDate._is_hebrew_leap_year(int(data["hy"])),
                days_in_month=int(data.get("hdm", 30))
            )
            
            # Cache result
            self._cache[cache_key] = (hebrew_date, datetime.now().timestamp())
            
            return hebrew_date
        
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Hebrew date response: {e}")
            raise DateConversionError(f"Invalid Hebrew date response: {e}") from e
    
    async def hebrew_to_gregorian(
        self,
        hebrew_date: Union[HebrewDate, str],
        target_year: Optional[int] = None
    ) -> date:
        """
        Convert Hebrew date to Gregorian date.
        
        Args:
            hebrew_date: Hebrew date to convert
            target_year: Specific Gregorian year to convert to (for recurring dates)
            
        Returns:
            date: Corresponding Gregorian date
            
        Raises:
            DateConversionError: If conversion fails
        """
        if isinstance(hebrew_date, str):
            hebrew_date = HebrewDate.from_string(hebrew_date)
        
        # If target_year specified, find the Hebrew date occurrence in that Gregorian year
        if target_year:
            cache_key = f"h2g_{hebrew_date.day}_{hebrew_date.month.value}_{target_year}"
        else:
            cache_key = f"h2g_{hebrew_date.day}_{hebrew_date.month.value}_{hebrew_date.year}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return cached_data
        
        try:
            params = {
                "hd": hebrew_date.day,
                "hm": hebrew_date.month.value,
                "h2g": "1"
            }
            
            if target_year:
                # Find Hebrew date occurrence in target Gregorian year
                # Try both possible Hebrew years that could map to this Gregorian year
                hebrew_year_1 = target_year + 3760
                hebrew_year_2 = target_year + 3761
                
                params["hy"] = hebrew_year_1
                data = await self._make_api_request(params)
                
                gregorian_date_1 = date(
                    int(data["gy"]),
                    int(data["gm"]),
                    int(data["gd"])
                )
                
                # If the first try gives us the target year, use it
                if gregorian_date_1.year == target_year:
                    result_date = gregorian_date_1
                else:
                    # Try the second Hebrew year
                    params["hy"] = hebrew_year_2
                    data = await self._make_api_request(params)
                    
                    result_date = date(
                        int(data["gy"]),
                        int(data["gm"]),
                        int(data["gd"])
                    )
            else:
                params["hy"] = hebrew_date.year
                data = await self._make_api_request(params)
                
                result_date = date(
                    int(data["gy"]),
                    int(data["gm"]),
                    int(data["gd"])
                )
            
            # Cache result
            self._cache[cache_key] = (result_date, datetime.now().timestamp())
            
            return result_date
        
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to parse Gregorian date response: {e}")
            raise DateConversionError(f"Invalid Gregorian date response: {e}") from e
    
    async def calculate_yahrzeit_date(
        self,
        death_date_hebrew: Union[HebrewDate, str]
    ) -> HebrewDate:
        """
        Calculate yahrzeit date (anniversary of death in Hebrew calendar).
        
        Yahrzeit is observed on the same Hebrew date each year.
        
        Args:
            death_date_hebrew: Hebrew date of death
            
        Returns:
            HebrewDate: Yahrzeit Hebrew date (same as death date)
        """
        if isinstance(death_date_hebrew, str):
            death_date_hebrew = HebrewDate.from_string(death_date_hebrew)
        
        # Yahrzeit is the same Hebrew date as death
        return HebrewDate(
            day=death_date_hebrew.day,
            month=death_date_hebrew.month,
            year=death_date_hebrew.year,  # This will be updated for specific year calculations
            formatted=f"{death_date_hebrew.day} {death_date_hebrew.month.value} (Yahrzeit)",
            is_leap_year=death_date_hebrew.is_leap_year,
            days_in_month=death_date_hebrew.days_in_month
        )
    
    async def get_next_yahrzeit(
        self,
        death_date_hebrew: Union[HebrewDate, str],
        from_date: Optional[date] = None
    ) -> Tuple[date, HebrewDate]:
        """
        Get the next yahrzeit (anniversary) date in Gregorian calendar.
        
        Args:
            death_date_hebrew: Hebrew date of death
            from_date: Date to calculate from (default: today)
            
        Returns:
            Tuple[date, HebrewDate]: Next yahrzeit in Gregorian and Hebrew calendars
            
        Raises:
            DateConversionError: If calculation fails
        """
        if isinstance(death_date_hebrew, str):
            death_date_hebrew = HebrewDate.from_string(death_date_hebrew)
        
        if not from_date:
            from_date = date.today()
        
        # Calculate yahrzeit Hebrew date
        yahrzeit_hebrew = await self.calculate_yahrzeit_date(death_date_hebrew)
        
        # Try current Gregorian year first
        current_year = from_date.year
        
        try:
            # Try current year
            yahrzeit_gregorian = await self.hebrew_to_gregorian(
                yahrzeit_hebrew,
                target_year=current_year
            )
            
            # If the date has already passed this year, get next year's date
            if yahrzeit_gregorian <= from_date:
                yahrzeit_gregorian = await self.hebrew_to_gregorian(
                    yahrzeit_hebrew,
                    target_year=current_year + 1
                )
            
            return yahrzeit_gregorian, yahrzeit_hebrew
        
        except DateConversionError:
            # Fallback: try next year
            yahrzeit_gregorian = await self.hebrew_to_gregorian(
                yahrzeit_hebrew,
                target_year=current_year + 1
            )
            
            return yahrzeit_gregorian, yahrzeit_hebrew
    
    async def get_hebrew_date_info(
        self,
        gregorian_date: Union[date, datetime]
    ) -> Dict[str, Any]:
        """
        Get comprehensive Hebrew date information for a Gregorian date.
        
        Args:
            gregorian_date: Gregorian date
            
        Returns:
            dict: Complete Hebrew date information including holidays, parsha, etc.
        """
        if isinstance(gregorian_date, datetime):
            gregorian_date = gregorian_date.date()
        
        cache_key = f"info_{gregorian_date.isoformat()}"
        
        # Check cache
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return cached_data
        
        try:
            hebrew_date = await self.gregorian_to_hebrew(gregorian_date)
            
            # Get additional information from HebCal API
            params = {
                "gd": gregorian_date.day,
                "gm": gregorian_date.month,
                "gy": gregorian_date.year,
                "g2h": "1",
                "i": "on",  # Include additional info
                "maj": "on",  # Major holidays
                "min": "on",  # Minor holidays
                "mod": "on",  # Modern holidays
                "nx": "on",  # Rosh Chodesh
                "mf": "on",  # Minor fasts
                "ss": "on",  # Special Shabbatot
            }
            
            data = await self._make_api_request(params)
            
            result = {
                "hebrew_date": hebrew_date.to_dict(),
                "gregorian_date": gregorian_date.isoformat(),
                "events": data.get("events", []),
                "holidays": [],
                "is_shabbat": gregorian_date.weekday() == 5,  # Saturday = 5
                "is_holiday": False,
                "parsha": None,
                "omer_day": data.get("omer"),
            }
            
            # Process events
            for event in data.get("events", []):
                if "holiday" in event.get("category", "").lower():
                    result["holidays"].append(event["title"])
                    result["is_holiday"] = True
                elif "parsha" in event.get("category", "").lower():
                    result["parsha"] = event["title"]
            
            # Cache result
            self._cache[cache_key] = (result, datetime.now().timestamp())
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to get Hebrew date info: {e}")
            # Return basic information if API fails
            hebrew_date = HebrewDate(
                day=1,
                month=HebrewMonth.TISHREI,
                year=gregorian_date.year + 3761,
                formatted=f"Hebrew date for {gregorian_date}",
                is_leap_year=False
            )
            
            return {
                "hebrew_date": hebrew_date.to_dict(),
                "gregorian_date": gregorian_date.isoformat(),
                "events": [],
                "holidays": [],
                "is_shabbat": gregorian_date.weekday() == 5,
                "is_holiday": False,
                "parsha": None,
                "omer_day": None,
                "error": str(e)
            }
    
    def format_hebrew_date(self, hebrew_date: HebrewDate, style: str = "full") -> str:
        """
        Format Hebrew date for display.
        
        Args:
            hebrew_date: Hebrew date to format
            style: Format style ('full', 'short', 'numeric')
            
        Returns:
            str: Formatted Hebrew date
        """
        if style == "numeric":
            return f"{hebrew_date.day}/{hebrew_date.month.value}/{hebrew_date.year}"
        elif style == "short":
            return f"{hebrew_date.day} {hebrew_date.month.value[:3]} {hebrew_date.year}"
        else:  # full
            return hebrew_date.formatted
    
    def validate_hebrew_date(self, date_string: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Hebrew date string format.
        
        Args:
            date_string: Hebrew date string to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            hebrew_date = HebrewDate.from_string(date_string)
            
            # Validate day range
            if not 1 <= hebrew_date.day <= 30:
                return False, "Day must be between 1 and 30"
            
            # Validate year range (reasonable range)
            if not 3000 <= hebrew_date.year <= 7000:
                return False, "Year must be between 3000 and 7000"
            
            return True, None
        
        except ValueError as e:
            return False, str(e)
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()


# Global service instance
_hebrew_calendar_service: Optional[HebrewCalendarService] = None


def get_hebrew_calendar_service() -> HebrewCalendarService:
    """
    Get Hebrew calendar service singleton.
    
    Returns:
        HebrewCalendarService: Service instance
    """
    global _hebrew_calendar_service
    if _hebrew_calendar_service is None:
        _hebrew_calendar_service = HebrewCalendarService()
    return _hebrew_calendar_service


async def cleanup_hebrew_calendar_service():
    """Clean up Hebrew calendar service resources."""
    global _hebrew_calendar_service
    if _hebrew_calendar_service:
        await _hebrew_calendar_service.close()
        _hebrew_calendar_service = None


# Utility functions for common operations
async def convert_gregorian_to_hebrew_string(
    gregorian_date: Union[date, datetime]
) -> str:
    """
    Quick utility to convert Gregorian date to Hebrew date string.
    
    Args:
        gregorian_date: Gregorian date to convert
        
    Returns:
        str: Formatted Hebrew date string
    """
    service = get_hebrew_calendar_service()
    
    async with service:
        hebrew_date = await service.gregorian_to_hebrew(gregorian_date)
        return service.format_hebrew_date(hebrew_date)


async def calculate_next_yahrzeit_date(
    death_date_hebrew: str,
    from_date: Optional[date] = None
) -> Optional[date]:
    """
    Quick utility to calculate next yahrzeit date.
    
    Args:
        death_date_hebrew: Hebrew death date string
        from_date: Date to calculate from (default: today)
        
    Returns:
        Optional[date]: Next yahrzeit date or None if calculation fails
    """
    try:
        service = get_hebrew_calendar_service()
        
        async with service:
            yahrzeit_gregorian, _ = await service.get_next_yahrzeit(
                death_date_hebrew,
                from_date
            )
            return yahrzeit_gregorian
    
    except Exception as e:
        logger.error(f"Failed to calculate next yahrzeit: {e}")
        return None