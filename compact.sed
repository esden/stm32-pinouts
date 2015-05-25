# ----
# Global Cleanup
# ----
# Remove commas in description
s/, / /g
# Remove annotations
s/([0-9])//g
# Remove EVENTOUT all io pins have it...
s/[ \/]*EVENTOUT//g
# Merge last and second to last cells (this does not work due to different amount of footprints...)
#s/^\([^ 	]\+\(	[^	]*\)\{12\}\)	\([^	]*\)$/\1 \3/
# Clean up white spaces that might get introduced in the last step
s/ *	 */	/g
# Remove all bracketed stuff
s/([^ 	]*)//g
# Remove the trailing details on pin names (this does not work due to different amount of footprints...)
#s/^\([^ 	]\+\(	[^	]*\)\{7\}\)	\([^	]*\)-[^ 	]\+/\1	\3/
#s/^\([^ 	]\+\(	[^	]*\)\{7\}\)	\([^	]*\)([^ 	]\+/\1	\3/

# ----
# Shorten function names
# ----
# Timers: TIMx_CHy -> TxCy
s/TIM\([0-9]\+\)_CH\([0-9]\+\)/T\1C\2/g
s/TIM\([0-9]\+\)_ETR/T\1E/g
s/TIM\([0-9]\+\)_BKIN/T\1BK/g

# ADC: ADCxxx_INyy -> ADCyy
s/ADC\([0-9]\+\)_IN\([0-9]\+\)/ADC\2/g
# DAC: DACxxx_OUTyy -> DACyy
s/DAC\([0-9]*\)_OUT\([0-9]\+\)/DAC\2/g

# Universal serial: UsARTx_func -> Uxfunc
s/USART\([0-9]\+\)_\([^ 	]\+\)/U\1\2/g
s/UART\([0-9]\+\)_\([^ 	]\+\)/U\1\2/g

# Trace
s/TRACE/TRA/g

# I2C
s/I2C\([0-9]\+\)_/I2C\1/g

# SPI
s/SPI\([0-9]\+\)_/S\1/g

# I2S
s/I2S\([0-9]\+\)_/I2S\1/g
s/I2S\([0-9]\+\)ext_/I2S\1e/g

# USB
s/OTG_HS_ULPI_/OHU/g
s/OTG_HS_/OH/g
s/OTG_FS_/OF/g

# Ethernet
s/ETH_MII_/EM/g
s/ETH_RMII_/ER/g
s/ETH_PPS_OUT/EPPSO/g
s/ETH_/E/g
s/\(E[RM]TX\)_EN/\1EN/g

# CAN
s/CAN\([0-9]\+\)_/C\1/g

# SDIO
s/SDIO_/SD/g

# DCMI
s/DCMI_/DC/g

# LCD
s/LCD_/L/g

# FMC
s/FMC_/FMC/g

# SAI
s/SAI\([0-9]\+\)_\([^ 	]\+\)_\([^ 	]\+\)/SA\1\2\3/g

# ----
# Final Cleanup
# ----

# Remove slashes in names
s/\// /g
# Fix the IO stuff
s/I O/I\/O/g
