#include "parametersview.h"
#include "ui_parametersview.h"

ParametersView::ParametersView(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::ParametersView)
{
    ui->setupUi(this);
}

ParametersView::~ParametersView()
{
    delete ui;
}
