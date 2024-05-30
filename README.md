# GeoAHSI (Geological mapper for AHSI)
光谱学可以根据矿物的电子跃迁和基团振动在反射太阳光谱范围（400-2500 nm）引起的吸收来识别它们。特别地，短波红外（SWIR）光谱区域（2000-2500 nm）是识别碳酸盐矿物和含水矿物（如云母和粘土）的关键光谱区间，它们通常是热液蚀变的产物，这就为遥感开展热液矿床勘探提供了理论基础。在世界范围内，遥感技术用于矿产勘查始于上世纪70年代，大部分研究关注于热液矿床勘探，有大量的文献详细阐述了遥感技术在这类矿床勘查中的应用。尤其是近三十年来随着高光谱成像技术的进步，高光谱遥感在矿产勘查领域取得了巨大的成功。自20世纪90年代起由Roger N. Clark等发展起来的Tetracorder矿物识别专家系统不断成熟完善，为高光谱矿物识别提供了强大的算法框架和基础工具。Tetracorder矿物识别方法已在美国西南部的多个荒漠地区通过Airborne Visible Infrared Imaging Spectrometer（AVIRIS-C）开展矿物填图应用得到验证。此外，Tetracorder在众多环境调查领域也显示出其有效性，证明了该方法的广泛适用性。近年来，美国启动了新一轮大规模高光谱矿物填图工作。根据《两党基础设施建设法案（BIL）》，美国国会在2022-2026年直接向美国地质调查局（USGS）提供5.107亿美元的资金，其中有1600万美元用于支持美国地质调查局（USGS）和美国国家航空和航天局（NASA）联合开展收集美国西部广大干旱半干旱地区的高光谱数据，并通过研究这些高光谱遥感数据中的岩矿“光谱特征”（Spectral Signatures），促进对基本地质框架的理解现代化，并提高对仍在地下和矿山废物中的关键矿产资源的了解，帮助寻找成矿潜力大的地区。

受历史上装备/数据源限制，国内并未系统性地开展西部地区高光谱遥感调查工作，找矿急需的蚀变填图工作程度很低，制约了找矿突破。从2018年起，国内陆续发射了高分五号等一系列技术参数达到国际领先水平的高光谱遥感卫星，为新一轮找矿突破战略行动提供了海量高光谱遥感数据，彻底解决了国内高光谱遥感矿产勘查应用“无米下锅”的窘境，也为“遥感先行”提供了新的契机。但是，一方面中西部地区典型热液矿床的高光谱遥感矿床定位模型与预测技术方法研究极度匮乏，直接限制了国产高光谱遥感卫星在支撑重点矿种找矿快速突破中的应用；另一方面，国内围绕国产高光谱遥感卫星地质应用还缺乏统一的技术规范，相关的软件工具难以见及，限制了国产高光谱遥感卫星数据的应用推广。

GeoAHSI是使用开源地理空间信息技术开发的一个面向国产高光谱遥感卫星矿物填图应用的纯Python工具包，它继承了Tetracorder系统的理论基础和算法。GeoAHSI的输入数据为经大气校正得到的地表反射率影像（ENVI Header格式），我们称其为Image Cube（m×n×k matrix，m代表行数，n代表列数，k代表波段数）。矿物填图分为三个步骤：首先，通过将Image Cube与从USGS Spectral Library 06（Clark et al. 2007）中筛选的参考矿物光谱进行匹配来计算它们的诊断光谱特征在Image Cube中的信号强度（相关性+吸收深度），得到Fit Cube（m×n×s matrix，s代表参考矿物光谱数量）和Depth Cube（m×n×s matrix）；然后，计算Fit Cube中沿第三维度（维数s）最大值对应的索引，降维得到Mineral Map（m×n matrix），并使用该索引检索Depth Cube得到Depth Map（m×n matrix）；最后，根据预设的颜色表为Mineral Map“赋色”，生成Color-Coded Map。在赋色的过程中，可以使用Depth Map经拉伸处理作为明度分量，从而呈现更加细腻的填图效果。




![屏幕截图 2023-06-28 190133](https://github.com/leecugb/pymica/assets/38849659/2a9aa593-e85f-4d86-8dd1-7ac3eb2671e0)
