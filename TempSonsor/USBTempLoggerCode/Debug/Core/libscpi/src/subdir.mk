################################################################################
# Automatically-generated file. Do not edit!
# Toolchain: GNU Tools for STM32 (12.3.rel1)
################################################################################

# Add inputs and outputs from these tool invocations to the build variables 
C_SRCS += \
../Core/libscpi/src/error.c \
../Core/libscpi/src/expression.c \
../Core/libscpi/src/fifo.c \
../Core/libscpi/src/ieee488.c \
../Core/libscpi/src/lexer.c \
../Core/libscpi/src/minimal.c \
../Core/libscpi/src/parser.c \
../Core/libscpi/src/units.c \
../Core/libscpi/src/utils.c 

OBJS += \
./Core/libscpi/src/error.o \
./Core/libscpi/src/expression.o \
./Core/libscpi/src/fifo.o \
./Core/libscpi/src/ieee488.o \
./Core/libscpi/src/lexer.o \
./Core/libscpi/src/minimal.o \
./Core/libscpi/src/parser.o \
./Core/libscpi/src/units.o \
./Core/libscpi/src/utils.o 

C_DEPS += \
./Core/libscpi/src/error.d \
./Core/libscpi/src/expression.d \
./Core/libscpi/src/fifo.d \
./Core/libscpi/src/ieee488.d \
./Core/libscpi/src/lexer.d \
./Core/libscpi/src/minimal.d \
./Core/libscpi/src/parser.d \
./Core/libscpi/src/units.d \
./Core/libscpi/src/utils.d 


# Each subdirectory must supply rules for building sources it contributes
Core/libscpi/src/%.o Core/libscpi/src/%.su Core/libscpi/src/%.cyclo: ../Core/libscpi/src/%.c Core/libscpi/src/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m0plus -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32L072xx -c -I../USB_DEVICE/App -I../Core/libscpi/inc -I../Core/libscpi/ -I../USB_DEVICE/Target -I../Core/Inc -I../Drivers/STM32L0xx_HAL_Driver/Inc -I../Drivers/STM32L0xx_HAL_Driver/Inc/Legacy -I../Middlewares/ST/STM32_USB_Device_Library/Core/Inc -I../Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc -I../Drivers/CMSIS/Device/ST/STM32L0xx/Include -I../Drivers/CMSIS/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-Core-2f-libscpi-2f-src

clean-Core-2f-libscpi-2f-src:
	-$(RM) ./Core/libscpi/src/error.cyclo ./Core/libscpi/src/error.d ./Core/libscpi/src/error.o ./Core/libscpi/src/error.su ./Core/libscpi/src/expression.cyclo ./Core/libscpi/src/expression.d ./Core/libscpi/src/expression.o ./Core/libscpi/src/expression.su ./Core/libscpi/src/fifo.cyclo ./Core/libscpi/src/fifo.d ./Core/libscpi/src/fifo.o ./Core/libscpi/src/fifo.su ./Core/libscpi/src/ieee488.cyclo ./Core/libscpi/src/ieee488.d ./Core/libscpi/src/ieee488.o ./Core/libscpi/src/ieee488.su ./Core/libscpi/src/lexer.cyclo ./Core/libscpi/src/lexer.d ./Core/libscpi/src/lexer.o ./Core/libscpi/src/lexer.su ./Core/libscpi/src/minimal.cyclo ./Core/libscpi/src/minimal.d ./Core/libscpi/src/minimal.o ./Core/libscpi/src/minimal.su ./Core/libscpi/src/parser.cyclo ./Core/libscpi/src/parser.d ./Core/libscpi/src/parser.o ./Core/libscpi/src/parser.su ./Core/libscpi/src/units.cyclo ./Core/libscpi/src/units.d ./Core/libscpi/src/units.o ./Core/libscpi/src/units.su ./Core/libscpi/src/utils.cyclo ./Core/libscpi/src/utils.d ./Core/libscpi/src/utils.o ./Core/libscpi/src/utils.su

.PHONY: clean-Core-2f-libscpi-2f-src

