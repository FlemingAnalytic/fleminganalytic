"""
Trading Router - Efficient Frontier and Portfolio Optimization
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
import yfinance as yf
from pypfopt import risk_models, expected_returns, EfficientFrontier, objective_functions
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Trading"])


class StrategyRequest(BaseModel):
    """Request model for trading strategy calculation"""
    ticker_portfolio: str = Field(..., description="Comma-separated ticker symbols (e.g., 'MSFT,AAPL,GOOGL,AMZN')")
    target_allocation: List[float] = Field(..., description="Target allocation percentages (e.g., [25, 25, 25, 25])")


class StrategyResponse(BaseModel):
    """Response model for trading strategy"""
    sp500_signal: dict
    avg_pe_ratio: dict
    avg_beta: dict
    efficient_frontier_picks: List[dict]


def get_demo_data(tickers: List[str]) -> StrategyResponse:
    """Return demo data when Yahoo Finance is unavailable"""
    logger.info("Yahoo Finance unavailable - returning demo data")

    # Create demo efficient frontier picks
    ef_picks = []
    # Distribute weights based on reverse order (for variety)
    total_weight = 100
    for i, ticker in enumerate(tickers):
        weight = round(total_weight / (len(tickers) - i), 2)
        if i == len(tickers) - 1:
            weight = round(total_weight, 2)  # Last ticker gets remaining weight
        ef_picks.append({
            "ticker": ticker,
            "weight": weight,
            "allocation": weight
        })
        total_weight -= weight

    return StrategyResponse(
        sp500_signal={
            "signal": "Demo Mode",
            "value": 0,
            "current": 0,
            "avg_200": 0
        },
        avg_pe_ratio={
            "value": None,
            "count": 0
        },
        avg_beta={
            "value": None,
            "count": 0
        },
        efficient_frontier_picks=ef_picks
    )


@router.post("/api/trading/strategy", response_model=StrategyResponse)
async def calculate_strategy(request: StrategyRequest):
    """
    Calculate trading strategy metrics including:
    - S&P 500 Signal
    - Average P/E Ratio of portfolio
    - Average Beta of portfolio
    - Efficient Frontier optimized picks
    """
    try:
        # Parse ticker portfolio
        tickers = [t.strip().upper() for t in request.ticker_portfolio.split(',') if t.strip()]

        if not tickers:
            raise HTTPException(status_code=400, detail="No valid tickers provided")

        if len(tickers) != len(request.target_allocation):
            raise HTTPException(
                status_code=400,
                detail=f"Number of tickers ({len(tickers)}) must match number of allocations ({len(request.target_allocation)})"
            )

        logger.info(f"Calculating strategy for tickers: {tickers}")

        # Download historical data (5 years for better estimation)
        # Use auto_adjust=True and add timeout for better reliability
        try:
            if len(tickers) == 1:
                # For single ticker, yfinance returns a DataFrame directly
                df_raw = yf.download(tickers[0], period='5y', progress=False, auto_adjust=True, timeout=30)
                if df_raw.empty:
                    raise HTTPException(status_code=400, detail=f"Unable to fetch data for {tickers[0]}")
                df = df_raw['Close'].to_frame()
                df.columns = [tickers[0]]
            else:
                # For multiple tickers
                df = yf.download(tickers, period='5y', progress=False, auto_adjust=True, timeout=30)['Close']
                if df.empty:
                    raise HTTPException(status_code=400, detail="Unable to fetch data for provided tickers")
        except Exception as e:
            logger.error(f"Error downloading data from Yahoo Finance: {e}")
            # Return demo data instead of failing
            return get_demo_data(tickers)

        # Calculate S&P 500 signal (fetch SPY for comparison)
        try:
            spy_data = yf.download('SPY', period='1y', progress=False, auto_adjust=True, timeout=30)['Close']
            spy_current = float(spy_data.iloc[-1])
            spy_avg_200 = float(spy_data.rolling(200).mean().iloc[-1])
            spy_signal = "Bullish" if spy_current > spy_avg_200 else "Bearish"
            spy_signal_value = round((spy_current / spy_avg_200 - 1) * 100, 2)
        except Exception as e:
            logger.warning(f"Could not fetch SPY data: {e}")
            spy_current = 0
            spy_avg_200 = 0
            spy_signal = "Unknown"
            spy_signal_value = 0

        # Calculate Average P/E Ratio and Beta
        pe_ratios = []
        betas = []

        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Get P/E ratio
                pe = info.get('trailingPE') or info.get('forwardPE')
                if pe and np.isfinite(pe):
                    pe_ratios.append(float(pe))

                # Get Beta
                beta = info.get('beta')
                if beta and np.isfinite(beta):
                    betas.append(float(beta))

            except Exception as e:
                logger.warning(f"Could not fetch metrics for {ticker}: {e}")
                continue

        avg_pe = round(np.mean(pe_ratios), 2) if pe_ratios else None
        avg_beta = round(np.mean(betas), 2) if betas else None

        # Calculate Efficient Frontier picks
        mu = expected_returns.mean_historical_return(df)
        S = risk_models.sample_cov(df)

        # Optimize for maximal Sharpe ratio
        ef = EfficientFrontier(mu, S)
        ef.add_objective(objective_functions.L2_reg, gamma=0.1)
        raw_weights = ef.max_sharpe()
        cleaned_weights = ef.clean_weights()

        # Get performance metrics
        performance = ef.portfolio_performance(verbose=False)
        expected_return = round(performance[0] * 100, 2)  # Convert to percentage
        volatility = round(performance[1] * 100, 2)  # Convert to percentage
        sharpe_ratio = round(performance[2], 2)

        # Create efficient frontier picks list
        ef_picks = []
        for ticker, weight in cleaned_weights.items():
            if weight > 0:  # Only include non-zero weights
                ef_picks.append({
                    "ticker": ticker,
                    "weight": round(weight * 100, 2),  # Convert to percentage
                    "allocation": round(weight * 100, 2)
                })

        # Sort by weight (highest first)
        ef_picks.sort(key=lambda x: x['weight'], reverse=True)

        return StrategyResponse(
            sp500_signal={
                "signal": spy_signal,
                "value": spy_signal_value,
                "current": round(spy_current, 2),
                "avg_200": round(spy_avg_200, 2)
            },
            avg_pe_ratio={
                "value": avg_pe,
                "count": len(pe_ratios)
            },
            avg_beta={
                "value": avg_beta,
                "count": len(betas)
            },
            efficient_frontier_picks=ef_picks
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating strategy: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating strategy: {str(e)}")


@router.get("/api/trading/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "trading"}
