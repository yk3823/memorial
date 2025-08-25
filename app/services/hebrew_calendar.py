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
        # Clean up the input string
        cleaned_string = cls._clean_hebrew_date_string(date_string)
        
        # This is a simplified parser - in production would need more robust parsing
        parts = cleaned_string.split()
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
    
    @classmethod
    def _clean_hebrew_date_string(cls, date_string: str) -> str:
        """
        Clean Hebrew date string by removing vowels, punctuation, and converting Hebrew numerals.
        
        Args:
            date_string: Raw Hebrew date string
            
        Returns:
            str: Cleaned date string in format "day month year"
        """
        import re
        
        # Remove Hebrew vowels (niqqud)
        vowels = '[\u05B0-\u05C7]'
        cleaned = re.sub(vowels, '', date_string)
        
        # Remove Hebrew punctuation marks
        punctuation = '[״׳]'
        cleaned = re.sub(punctuation, '', cleaned)
        
        # Hebrew numerals mapping (common ones)
        hebrew_numerals = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
            'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
            'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400
        }
        
        # Special Hebrew numerals combinations
        special_numerals = {
            'טו': 15, 'טז': 16,  # 15 and 16 (not יה and יו for religious reasons)
            'כט': 29, 'ל': 30,
        }
        
        # Hebrew month names mapping
        month_mapping = {
            'תשרי': 'Tishrei',
            'חשון': 'Cheshvan', 'חשוון': 'Cheshvan', 'מרחשון': 'Cheshvan',
            'כסלו': 'Kislev', 'כסלה': 'Kislev',
            'טבת': 'Tevet',
            'שבט': 'Shevat',
            'אדר': 'Adar', 'אדרא': 'Adar', 'אדרב': 'Adar II',
            'ניסן': 'Nissan',
            'אייר': 'Iyar',
            'סיון': 'Sivan', 'סיוון': 'Sivan',
            'תמוז': 'Tamuz',
            'אב': 'Av', 'אבא': 'Av', 'מנאב': 'Av',
            'אלול': 'Elul'
        }
        
        # Hebrew year prefixes
        hebrew_years = {
            'תש': 5700, 'תשע': 5770, 'תשף': 5780, 'תשפ': 5780, 'תשצ': 5790,
            'תשפא': 5781, 'תשפב': 5782, 'תשפג': 5783, 'תשפד': 5784, 'תשפה': 5785
        }
        
        # Split into parts
        parts = cleaned.split()
        result_parts = []
        
        for part in parts:
            # Try to convert Hebrew numerals to Arabic numerals
            if re.match(r'^[א-ת]+$', part):
                # Check if it's a year prefix
                year_converted = False
                for prefix, base_year in hebrew_years.items():
                    if part.startswith(prefix):
                        remaining = part[len(prefix):]
                        if remaining:
                            additional = sum(hebrew_numerals.get(char, 0) for char in remaining)
                            result_parts.append(str(base_year + additional))
                            year_converted = True
                            break
                
                if not year_converted:
                    # Check if it's a month name FIRST (before numeral conversion)
                    month_found = False
                    for heb_month, eng_month in month_mapping.items():
                        if heb_month == part or heb_month in part or part in heb_month:
                            result_parts.append(eng_month)
                            month_found = True
                            break
                    
                    if not month_found:
                        # Check special numerals
                        if part in special_numerals:
                            result_parts.append(str(special_numerals[part]))
                        else:
                            # Try to convert as regular Hebrew numeral
                            numeral_value = sum(hebrew_numerals.get(char, 0) for char in part)
                            if numeral_value > 0:
                                result_parts.append(str(numeral_value))
                            else:
                                result_parts.append(part)
            else:
                result_parts.append(part)
        
        return ' '.join(result_parts)
    
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
        death_date_gregorian: Optional[date] = None,
        from_date: Optional[date] = None,
        yahrzeit_custom: int = 3
    ) -> Tuple[date, HebrewDate, bool]:
        """
        Get the next yahrzeit (anniversary) date in Gregorian calendar.
        
        Yahrzeit rules based on custom:
        - yahrzeit_custom = 1 (Sephardic): First year = 11 months, subsequent = 12 months
        - yahrzeit_custom = 2 (Ashkenazi): Always 12 months 
        - yahrzeit_custom = 3 (General): Always 12 months
        
        Args:
            death_date_hebrew: Hebrew date of death
            death_date_gregorian: Gregorian date of death (for determining first year)
            from_date: Date to calculate from (default: today)
            yahrzeit_custom: Custom rule (1=Sephardic, 2=Ashkenazi, 3=General)
            
        Returns:
            Tuple[date, HebrewDate, bool]: Next yahrzeit in Gregorian, Hebrew calendars, and is_first_year
            
        Raises:
            DateConversionError: If calculation fails
        """
        if isinstance(death_date_hebrew, str):
            death_date_hebrew = HebrewDate.from_string(death_date_hebrew)
        
        if not from_date:
            from_date = date.today()
        
        # If no gregorian death date provided, try to get it from hebrew date
        if not death_date_gregorian and death_date_hebrew:
            try:
                death_date_gregorian = await self.hebrew_to_gregorian(death_date_hebrew)
            except DateConversionError:
                death_date_gregorian = from_date  # Fallback
        
        # Determine if this is the first year
        is_first_year = False
        if death_date_gregorian:
            # Check if we're within the first Hebrew year (approximately 13 months)
            first_yahrzeit_cutoff = death_date_gregorian + timedelta(days=380)  # ~13 months
            is_first_year = from_date <= first_yahrzeit_cutoff
        
        # Calculate yahrzeit Hebrew date based on custom rules
        if is_first_year and yahrzeit_custom == 1:
            # Sephardic custom: First year = 11 Hebrew months from death
            yahrzeit_hebrew = await self._add_hebrew_months(death_date_hebrew, 11)
        else:
            # All other cases: 12 months (same Hebrew date annually)
            # This covers: Ashkenazi, General, or subsequent years for Sephardic
            yahrzeit_hebrew = HebrewDate(
                day=death_date_hebrew.day,
                month=death_date_hebrew.month,
                year=death_date_hebrew.year,  # Will be updated for specific year calculations
                formatted=f"{death_date_hebrew.day} {death_date_hebrew.month.value} (יארצייט)",
                is_leap_year=death_date_hebrew.is_leap_year,
                days_in_month=death_date_hebrew.days_in_month
            )
        
        # Convert to Gregorian date for current/next year
        current_year = from_date.year
        
        try:
            # Try current year first
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
                # Update Hebrew date year to match the calculated year
                yahrzeit_hebrew = await self.gregorian_to_hebrew(yahrzeit_gregorian)
            
            return yahrzeit_gregorian, yahrzeit_hebrew, is_first_year
        
        except DateConversionError:
            # Fallback: try next year
            yahrzeit_gregorian = await self.hebrew_to_gregorian(
                yahrzeit_hebrew,
                target_year=current_year + 1
            )
            # Update Hebrew date year to match the calculated year
            yahrzeit_hebrew = await self.gregorian_to_hebrew(yahrzeit_gregorian)
            
            return yahrzeit_gregorian, yahrzeit_hebrew, is_first_year
    
    async def get_sephardic_memorial_dates(
        self,
        death_date_hebrew: Union[HebrewDate, str],
        death_date_gregorian: Optional[date] = None,
        from_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get both Azkara (11 months) and Yahrzeit (12 months) dates for Sephardic custom.
        
        Sephardic Jews observe two separate dates in the first year:
        1. אזכרה (Azkara) - Memorial at 11 Hebrew months
        2. יארצייט (Yahrzeit) - Anniversary at 12 Hebrew months (same Hebrew date annually)
        
        Args:
            death_date_hebrew: Hebrew date of death
            death_date_gregorian: Gregorian date of death (for determining first year)
            from_date: Date to calculate from (default: today)
            
        Returns:
            Dict with both Azkara and Yahrzeit information
        """
        if isinstance(death_date_hebrew, str):
            death_date_hebrew = HebrewDate.from_string(death_date_hebrew)
        
        if not from_date:
            from_date = date.today()
        
        # If no gregorian death date provided, try to get it from hebrew date
        if not death_date_gregorian and death_date_hebrew:
            try:
                death_date_gregorian = await self.hebrew_to_gregorian(death_date_hebrew)
            except DateConversionError:
                death_date_gregorian = from_date  # Fallback
        
        # Determine if this is the first year
        is_first_year = False
        if death_date_gregorian:
            # Check if we're within the first Hebrew year (approximately 13 months)
            first_yahrzeit_cutoff = death_date_gregorian + timedelta(days=380)  # ~13 months
            is_first_year = from_date <= first_yahrzeit_cutoff
        
        result = {
            "is_first_year": is_first_year,
            "death_date_hebrew": death_date_hebrew,
            "death_date_gregorian": death_date_gregorian
        }
        
        try:
            # Calculate Azkara (11 months) - always calculated for Sephardic
            azkara_hebrew = await self._add_hebrew_months(death_date_hebrew, 11)
            current_year = from_date.year
            
            # Convert Azkara to Gregorian
            azkara_gregorian = await self.hebrew_to_gregorian(
                azkara_hebrew,
                target_year=current_year
            )
            
            # If Azkara has passed this year, get next year's date
            if azkara_gregorian <= from_date:
                azkara_gregorian = await self.hebrew_to_gregorian(
                    azkara_hebrew,
                    target_year=current_year + 1
                )
            
            # Calculate days until Azkara
            days_until_azkara = (azkara_gregorian - from_date).days
            
            result["azkara"] = {
                "gregorian_date": azkara_gregorian.isoformat(),
                "hebrew_date": {
                    "formatted": f"{self.format_hebrew_date(azkara_hebrew, style='hebrew')} (אזכרה)",
                    "day": azkara_hebrew.day,
                    "month": azkara_hebrew.month.value,
                    "year": azkara_hebrew.year,
                    "is_leap_year": azkara_hebrew.is_leap_year
                },
                "days_until": days_until_azkara,
                "gregorian_formatted": {
                    "hebrew": f"{azkara_gregorian.day}/{azkara_gregorian.month}/{azkara_gregorian.year}",
                    "full": azkara_gregorian.strftime("%d/%m/%Y")
                },
                "months_calculated": 11
            }
            
            # Calculate Yahrzeit (12 months / same Hebrew date annually)
            yahrzeit_hebrew = HebrewDate(
                day=death_date_hebrew.day,
                month=death_date_hebrew.month,
                year=death_date_hebrew.year,  # Will be updated for specific year calculations
                formatted=f"{death_date_hebrew.day} {death_date_hebrew.month.value} (יארצייט)",
                is_leap_year=death_date_hebrew.is_leap_year,
                days_in_month=death_date_hebrew.days_in_month
            )
            
            # Convert Yahrzeit to Gregorian
            yahrzeit_gregorian = await self.hebrew_to_gregorian(
                yahrzeit_hebrew,
                target_year=current_year
            )
            
            # If Yahrzeit has passed this year, get next year's date
            if yahrzeit_gregorian <= from_date:
                yahrzeit_gregorian = await self.hebrew_to_gregorian(
                    yahrzeit_hebrew,
                    target_year=current_year + 1
                )
            
            # Calculate days until Yahrzeit
            days_until_yahrzeit = (yahrzeit_gregorian - from_date).days
            
            result["yahrzeit"] = {
                "gregorian_date": yahrzeit_gregorian.isoformat(),
                "hebrew_date": {
                    "formatted": f"{self.format_hebrew_date(yahrzeit_hebrew, style='hebrew')} (יארצייט)",
                    "day": yahrzeit_hebrew.day,
                    "month": yahrzeit_hebrew.month.value,
                    "year": yahrzeit_hebrew.year,
                    "is_leap_year": yahrzeit_hebrew.is_leap_year
                },
                "days_until": days_until_yahrzeit,
                "gregorian_formatted": {
                    "hebrew": f"{yahrzeit_gregorian.day}/{yahrzeit_gregorian.month}/{yahrzeit_gregorian.year}",
                    "full": yahrzeit_gregorian.strftime("%d/%m/%Y")
                },
                "months_calculated": 12
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating Sephardic memorial dates: {e}")
            raise DateConversionError(f"Failed to calculate Sephardic memorial dates: {e}") from e
    
    async def _add_hebrew_months(self, hebrew_date: HebrewDate, months: int) -> HebrewDate:
        """
        Add months to a Hebrew date.
        
        Args:
            hebrew_date: Starting Hebrew date
            months: Number of months to add
            
        Returns:
            HebrewDate: New date with months added
        """
        # This is a simplified implementation
        # In practice, you'd need to handle Hebrew calendar complexities
        new_month_index = list(HebrewMonth).index(hebrew_date.month) + months
        new_year = hebrew_date.year
        
        # Handle year overflow
        while new_month_index >= 13:  # Assuming max 13 months in leap year
            new_month_index -= 12  # Regular year has 12 months
            new_year += 1
            # Check if new year is leap year and adjust accordingly
            if HebrewDate._is_hebrew_leap_year(new_year):
                if new_month_index >= 13:
                    new_month_index -= 1
        
        while new_month_index < 0:
            new_month_index += 12
            new_year -= 1
        
        # Get the month enum
        hebrew_months = list(HebrewMonth)
        new_month = hebrew_months[min(new_month_index, len(hebrew_months) - 1)]
        
        return HebrewDate(
            day=hebrew_date.day,
            month=new_month,
            year=new_year,
            formatted=f"{hebrew_date.day} {new_month.value} {new_year}",
            is_leap_year=HebrewDate._is_hebrew_leap_year(new_year)
        )
    
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
    
    def _number_to_hebrew(self, number: int, is_year: bool = False) -> str:
        """Convert number to Hebrew numeral representation."""
        if number <= 0:
            return str(number)
        
        # For Hebrew years, use abbreviated form (last 3 digits)
        if is_year and number > 5000:
            # Extract last 3 digits for Hebrew year abbreviation
            last_digits = number % 1000
            return self._convert_small_number_to_hebrew(last_digits)
        else:
            return self._convert_small_number_to_hebrew(number)
    
    def _convert_small_number_to_hebrew(self, number: int) -> str:
        """Convert small numbers (under 1000) to Hebrew numerals."""
        if number <= 0:
            return str(number)
        
        # Hebrew numerals mapping
        hebrew_numerals = [
            (400, 'ת'), (300, 'ש'), (200, 'ר'), (100, 'ק'),
            (90, 'צ'), (80, 'פ'), (70, 'ע'), (60, 'ס'), (50, 'נ'), 
            (40, 'מ'), (30, 'ל'), (20, 'כ'), (19, 'יט'), (18, 'יח'),
            (17, 'יז'), (16, 'טז'), (15, 'טו'), (10, 'י'),
            (9, 'ט'), (8, 'ח'), (7, 'ז'), (6, 'ו'), (5, 'ה'),
            (4, 'ד'), (3, 'ג'), (2, 'ב'), (1, 'א')
        ]
        
        result = ""
        remaining = number
        
        for value, letter in hebrew_numerals:
            if remaining >= value:
                count = remaining // value
                result += letter * count
                remaining -= value * count
        
        # Add geresh (׳) for single letter or gershayim (״) for multiple letters
        if len(result) == 1:
            result += '׳'
        elif len(result) > 1:
            result = result[:-1] + '״' + result[-1]
            
        return result
    
    def _get_hebrew_month_name(self, month: HebrewMonth) -> str:
        """Get Hebrew name for month."""
        hebrew_months = {
            HebrewMonth.TISHREI: 'תשרי',
            HebrewMonth.CHESHVAN: 'חשון', 
            HebrewMonth.KISLEV: 'כסלו',
            HebrewMonth.TEVET: 'טבת',
            HebrewMonth.SHEVAT: 'שבט',
            HebrewMonth.ADAR: 'אדר',
            HebrewMonth.ADAR_II: 'אדר ב׳',
            HebrewMonth.NISSAN: 'ניסן',
            HebrewMonth.IYAR: 'אייר',
            HebrewMonth.SIVAN: 'סיון',
            HebrewMonth.TAMUZ: 'תמוז',
            HebrewMonth.AV: 'אב',
            HebrewMonth.ELUL: 'אלול'
        }
        return hebrew_months.get(month, month.value)
    
    def format_hebrew_date(self, hebrew_date: HebrewDate, style: str = "full") -> str:
        """
        Format Hebrew date for display.
        
        Args:
            hebrew_date: Hebrew date to format
            style: Format style ('full', 'short', 'numeric', 'hebrew')
            
        Returns:
            str: Formatted Hebrew date
        """
        if style == "numeric":
            return f"{hebrew_date.day}/{hebrew_date.month.value}/{hebrew_date.year}"
        elif style == "short":
            return f"{hebrew_date.day} {hebrew_date.month.value[:3]} {hebrew_date.year}"
        elif style == "hebrew":
            # Full Hebrew format with Hebrew numerals
            day_hebrew = self._number_to_hebrew(hebrew_date.day)
            month_hebrew = self._get_hebrew_month_name(hebrew_date.month)
            year_hebrew = self._number_to_hebrew(hebrew_date.year, is_year=True)
            return f"{day_hebrew} {month_hebrew} {year_hebrew}"
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